import { NextRequest, NextResponse } from 'next/server';

interface RAGRequest {
  query: string;
  documents?: string[];
  limit?: number;
  model?: string;
  includeReferences?: boolean;
  language?: string;
}

interface SemanticResult {
  chunk_id: string;
  document_id: number;
  document_title: string;
  document_author: string;
  text: string;
  similarity: number;
  chunk_index: number;
  metadata: any;
}

interface RAGResponse {
  query: string;
  answer: string;
  sources: Array<{
    id: string;
    title: string;
    author: string;
    text: string;
    similarity: number;
    reference: string;
  }>;
  model_used: string;
  processing_time_ms: number;
}

const PYTHON_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Lista de endpoints de AI disponibles
const AI_ENDPOINTS = {
  'novita': process.env.NOVITA_API_URL,
  'kimi': process.env.KIMI_API_URL,
  'openai': process.env.OPENAI_API_URL || 'https://api.openai.com/v1',
  'local': 'http://localhost:11434' // Ollama local
};

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    const body: RAGRequest = await request.json();
    
    // Validar entrada
    if (!body.query || typeof body.query !== 'string') {
      return NextResponse.json(
        { error: 'Query is required and must be a string' },
        { status: 400 }
      );
    }

    const query = body.query.trim();
    const limit = body.limit || 8;
    const model = body.model || 'openai';
    const includeReferences = body.includeReferences !== false;
    const language = body.language || 'es';

    // 1. Realizar búsqueda semántica
    console.log('Performing semantic search for:', query);
    
    const semanticResponse = await fetch(`${PYTHON_API_URL}/api/search/semantic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        limit: limit,
        document_ids: body.documents
      }),
    });

    if (!semanticResponse.ok) {
      throw new Error(`Semantic search failed: ${semanticResponse.status}`);
    }

    const semanticResults: SemanticResult[] = await semanticResponse.json();
    
    if (!semanticResults || semanticResults.length === 0) {
      return NextResponse.json({
        query,
        answer: "No encontré información relevante en la biblioteca para responder a tu pregunta.",
        sources: [],
        model_used: model,
        processing_time_ms: Date.now() - startTime
      } as RAGResponse);
    }

    // 2. Preparar contexto para el LLM
    const contextChunks = semanticResults.map((result, index) => {
      const reference = `[${index + 1}] "${result.document_title}" por ${result.document_author}, página ${result.chunk_index + 1}`;
      return {
        reference,
        text: result.text,
        ...result
      };
    });

    // 3. Construir prompt para el LLM
    const prompt = buildRAGPrompt(query, contextChunks, language, includeReferences);

    // 4. Llamar al LLM
    console.log('Calling LLM with model:', model);
    const llmResponse = await callLLM(prompt, model);

    // 5. Preparar respuesta
    const sources = contextChunks.map((chunk, index) => ({
      id: chunk.chunk_id,
      title: chunk.document_title,
      author: chunk.document_author,
      text: chunk.text,
      similarity: chunk.similarity,
      reference: chunk.reference
    }));

    const response: RAGResponse = {
      query,
      answer: llmResponse,
      sources,
      model_used: model,
      processing_time_ms: Date.now() - startTime
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Error in RAG endpoint:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

function buildRAGPrompt(query: string, contextChunks: any[], language: string, includeReferences: boolean): string {
  const context = contextChunks.map((chunk, index) => {
    return `${chunk.reference}:\n${chunk.text}\n`;
  }).join('\n---\n\n');

  const referencesInstruction = includeReferences 
    ? "IMPORTANTE: Siempre incluye las referencias específicas en tu respuesta usando el formato [1], [2], etc. para citar las fuentes exactas."
    : "";

  if (language === 'es') {
    return `Eres un asistente experto en literatura y filosofía. Responde a la pregunta basándote ÚNICAMENTE en la información proporcionada a continuación.

${referencesInstruction}

CONTEXTO DE LA BIBLIOTECA:
${context}

PREGUNTA: ${query}

INSTRUCCIONES:
- Responde de manera clara y precisa
- Usa solo la información del contexto proporcionado
- Si no tienes suficiente información, dilo claramente
- Mantén un tono académico pero accesible
- ${includeReferences ? 'Cita las fuentes usando [1], [2], etc.' : 'No necesitas citar fuentes'}

RESPUESTA:`;
  } else {
    return `You are an expert assistant in literature and philosophy. Answer the question based ONLY on the information provided below.

${referencesInstruction}

LIBRARY CONTEXT:
${context}

QUESTION: ${query}

INSTRUCTIONS:
- Answer clearly and precisely
- Use only the information from the provided context
- If you don't have enough information, state it clearly
- Maintain an academic but accessible tone
- ${includeReferences ? 'Cite sources using [1], [2], etc.' : 'No need to cite sources'}

ANSWER:`;
  }
}

async function callLLM(prompt: string, model: string): Promise<string> {
  switch (model) {
    case 'openai':
      return await callOpenAI(prompt);
    case 'novita':
      return await callNovita(prompt);
    case 'kimi':
      return await callKimi(prompt);
    case 'local':
      return await callOllama(prompt);
    default:
      throw new Error(`Unsupported model: ${model}`);
  }
}

async function callOpenAI(prompt: string): Promise<string> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OpenAI API key not configured');
  }

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 1500,
      temperature: 0.3
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices[0]?.message?.content || 'No response from OpenAI';
}

async function callNovita(prompt: string): Promise<string> {
  const apiKey = process.env.NOVITA_API_KEY;
  const baseUrl = process.env.NOVITA_API_URL || 'https://api.novita.ai/v3';
  
  if (!apiKey) {
    throw new Error('Novita API key not configured');
  }

  const response = await fetch(`${baseUrl}/openai/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'meta-llama/llama-3.1-8b-instruct',
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 1500,
      temperature: 0.3
    }),
  });

  if (!response.ok) {
    throw new Error(`Novita API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices[0]?.message?.content || 'No response from Novita';
}

async function callKimi(prompt: string): Promise<string> {
  const apiKey = process.env.KIMI_API_KEY;
  const baseUrl = process.env.KIMI_API_URL || 'https://api.moonshot.cn/v1';
  
  if (!apiKey) {
    throw new Error('Kimi API key not configured');
  }

  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'moonshot-v1-8k',
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 1500,
      temperature: 0.3
    }),
  });

  if (!response.ok) {
    throw new Error(`Kimi API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices[0]?.message?.content || 'No response from Kimi';
}

async function callOllama(prompt: string): Promise<string> {
  const baseUrl = 'http://localhost:11434';
  
  const response = await fetch(`${baseUrl}/api/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'llama3.1:8b',
      prompt: prompt,
      stream: false,
      options: {
        temperature: 0.3,
        num_predict: 1500
      }
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama API error: ${response.status}`);
  }

  const data = await response.json();
  return data.response || 'No response from Ollama';
}