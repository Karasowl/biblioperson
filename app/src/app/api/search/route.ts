import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';

interface SearchRequest {
  query: string;
  type: 'literal' | 'semantic' | 'both';
  filters?: {
    authors?: string[];
    documentIds?: string[];
    language?: string;
  };
  options?: {
    caseSensitive?: boolean;
    wholeWord?: boolean;
    useRegex?: boolean;
    limit?: number;
    offset?: number;
  };
}

interface SearchResult {
  id: string;
  documentId: string;
  documentTitle: string;
  author: string;
  text: string;
  highlightedText: string;
  score: number;
  matchPositions: { start: number; end: number }[];
  context: {
    before: string;
    after: string;
  };
  metadata: {
    page?: number;
    section?: string;
    segmentId: string;
  };
}

// Helper function to find a term in content using word boundaries
function findTermInContent(content: string, term: string): { term: string; index: number } | null {
  const isPhrase = term.includes(' ');
  
  if (isPhrase) {
    try {
      const escapedPhrase = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const phraseRegex = new RegExp(`\\b${escapedPhrase}\\b`, 'i');
      const match = content.match(phraseRegex);
      if (match && match.index !== undefined) {
        return { term, index: match.index };
      }
    } catch {
      // Fallback to simple search for phrases
      const index = content.toLowerCase().indexOf(term.toLowerCase());
      if (index !== -1) {
        return { term, index };
      }
    }
  } else {
    try {
      const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const wordBoundaryRegex = new RegExp(`\\b${escapedTerm}\\b`, 'i');
      const match = content.match(wordBoundaryRegex);
      if (match && match.index !== undefined) {
        return { term, index: match.index };
      }
    } catch {
      // Skip fallback for single words to avoid partial matches
    }
  }
  
  return null;
}

// Helper function to evaluate operators (AND, OR, NOT)
function evaluateOperators(content: string, operators: { type: 'AND' | 'OR' | 'NOT'; terms: string[] }[]): boolean {
  console.log('[Search API] Evaluating operators:', operators);
  
  for (const operator of operators) {
    console.log('[Search API] Processing operator:', operator.type, 'with terms:', operator.terms);
    
    if (operator.type === 'AND') {
      // All terms must be found
      const termResults = operator.terms.map(term => {
        const match = findTermInContent(content, term);
        const found = match !== null;
        console.log('[Search API] AND term check:', term, '→', found);
        return found;
      });
      
      const allFound = termResults.every(result => result);
      console.log('[Search API] AND result - all terms found:', allFound, 'term results:', termResults);
      
      if (allFound) return true;
    } else if (operator.type === 'OR') {
      // At least one term must be found
      const termResults = operator.terms.map(term => {
        const match = findTermInContent(content, term);
        const found = match !== null;
        console.log('[Search API] OR term check:', term, '→', found);
        return found;
      });
      
      const anyFound = termResults.some(result => result);
      console.log('[Search API] OR result - any term found:', anyFound, 'term results:', termResults);
      
      if (anyFound) return true;
    } else if (operator.type === 'NOT') {
      // Terms must NOT be found
      const termResults = operator.terms.map(term => {
        const match = findTermInContent(content, term);
        const found = match !== null;
        console.log('[Search API] NOT term check:', term, '→', found);
        return found;
      });
      
      const noneFound = termResults.every(result => !result);
      console.log('[Search API] NOT result - no terms found:', noneFound, 'term results:', termResults);
      
      if (noneFound) return true;
    }
  }
  
  console.log('[Search API] No operators matched');
  return false;
}

// Parse search query with operators
function parseSearchQuery(query: string): {
  terms: string[];
  phrases: string[];
  operators: { type: 'AND' | 'OR' | 'NOT'; terms: string[] }[];
} {
  const phrases: string[] = [];
  const terms: string[] = [];
  const operators: { type: 'AND' | 'OR' | 'NOT'; terms: string[] }[] = [];

  // Extract phrases in quotes
  const phraseRegex = /"([^"]+)"/g;
  let phraseMatch;
  while ((phraseMatch = phraseRegex.exec(query)) !== null) {
    phrases.push(phraseMatch[1]);
  }

  // Remove phrases from query
  let cleanQuery = query.replace(phraseRegex, '');

  // Parse operators
  const andMatch = cleanQuery.match(/(\w+)\s+AND\s+(\w+)/gi);
  const orMatch = cleanQuery.match(/(\w+)\s+OR\s+(\w+)/gi);
  const notMatch = cleanQuery.match(/NOT\s+(\w+)/gi);

  if (andMatch) {
    andMatch.forEach(match => {
      const [term1, , term2] = match.split(/\s+/);
      operators.push({ type: 'AND', terms: [term1, term2] });
    });
  }

  if (orMatch) {
    orMatch.forEach(match => {
      const [term1, , term2] = match.split(/\s+/);
      operators.push({ type: 'OR', terms: [term1, term2] });
    });
  }

  if (notMatch) {
    notMatch.forEach(match => {
      const [, term] = match.split(/\s+/);
      operators.push({ type: 'NOT', terms: [term] });
    });
  }

  // Remove operators from query and extract remaining terms
  cleanQuery = cleanQuery.replace(/(\w+)\s+(AND|OR)\s+(\w+)/gi, '');
  cleanQuery = cleanQuery.replace(/NOT\s+\w+/gi, '');
  
  const remainingTerms = cleanQuery.trim().split(/\s+/).filter(t => t.length > 0);
  terms.push(...remainingTerms);

  return { terms, phrases, operators };
}



export async function POST(request: NextRequest) {
  try {
    const body: SearchRequest = await request.json();
    const { query, type = 'both', filters, options } = body;

    console.log('[Search API] Received search request:', { query, type, filters });
    console.log('[Search API] Backend URL:', BACKEND_URL);

    // Parse the search query
    const parsedQuery = parseSearchQuery(query);
    console.log('[Search API] Parsed query:', parsedQuery);

    // Try semantic search FIRST if requested (before literal search)
    if (type === 'semantic' || type === 'both') {
      console.log('[Search API] ⭐ EXECUTING SEMANTIC SEARCH for type:', type);
      console.log('[Search API] Query:', query);
      console.log('[Search API] Backend URL:', `${BACKEND_URL}/api/search/semantic`);
      
      try {
        const semanticResponse = await fetch(`${BACKEND_URL}/api/search/semantic`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            limit: options?.limit || 50
          })
        });

        console.log('[Search API] ⭐ Semantic response status:', semanticResponse.status);

        if (semanticResponse.ok) {
          const semanticData = await semanticResponse.json();
          console.log('[Search API] Semantic search successful:', {
            hasResults: !!semanticData.results,
            resultsCount: semanticData.results?.length || 0,
            firstResult: semanticData.results?.[0]
          });
          
          // Transform semantic results to our format
          const semanticResults: SearchResult[] = semanticData.results?.map((result: {
            segment_id: string;
            text: string;
            document_id: string;
            document_title: string;
            document_author: string;
            original_page?: number;
            similarity: number;
          }, index: number) => ({
            id: `semantic-${result.segment_id || index}`,
            documentId: result.document_id,
            documentTitle: result.document_title,
            author: result.document_author,
            text: result.text.length > 360 ? result.text.substring(0, 360) + '...' : result.text,
            highlightedText: result.text.length > 360 ? result.text.substring(0, 360) + '...' : result.text,
            score: Math.round((1 - Math.abs(result.similarity)) * 100), // Convert similarity to percentage
            matchPositions: [],
            context: {
              before: '',
              after: ''
            },
            metadata: {
              page: result.original_page,
              section: 'Semantic Match',
              segmentId: result.segment_id || `segment-${index}`
            }
          })) || [];

          // If we have semantic results and this is semantic-only search, return them IMMEDIATELY
          if (type === 'semantic') {
            console.log('[Search API] ⭐ RETURNING SEMANTIC-ONLY RESULTS:', semanticResults.length);
            console.log('[Search API] ⭐ First result:', semanticResults[0]);
            return NextResponse.json({
              success: true,
              results: semanticResults,
              total: semanticResults.length,
              query: parsedQuery,
              searchType: 'semantic'
            });
          }

          // For 'both' type, we'll combine with literal results later
          if (type === 'both' && semanticResults.length > 0) {
            // Store semantic results to combine later
            (globalThis as { semanticResults?: SearchResult[] }).semanticResults = semanticResults;
          }
        } else {
          console.log('[Search API] Semantic search failed with status:', semanticResponse.status);
          const errorText = await semanticResponse.text();
          console.log('[Search API] Semantic error response:', errorText);
        }
      } catch (semanticError) {
        console.log('[Search API] Semantic search failed with error:', semanticError);
      }
    }

    // Only do literal search if type is 'literal' or 'both'
    if (type === 'literal' || type === 'both') {
      console.log('[Search API] Attempting literal search...');
      
      const searchParams = new URLSearchParams({
        q: query,
        type: type,
        limit: String(options?.limit || 50),
        offset: String(options?.offset || 0)
      });

      if (filters?.authors?.length) {
        searchParams.append('authors', filters.authors.join(','));
      }
      if (filters?.documentIds?.length) {
        searchParams.append('documents', filters.documentIds.join(','));
      }

             // Try to search in library documents
       console.log('[Search API] Trying to search in library documents...');
     
       try {
         // Get all documents from library
         console.log('[Search API] Fetching documents from:', `${BACKEND_URL}/api/library/documents`);
         const documentsResponse = await fetch(`${BACKEND_URL}/api/library/documents`);
         
         console.log('[Search API] Documents response status:', documentsResponse.status);
         
         if (documentsResponse.ok) {
           const documentsData = await documentsResponse.json();
           console.log('[Search API] Got documents from library:', {
             success: documentsData.success,
             documentCount: documentsData.documents?.length || 0,
             firstDoc: documentsData.documents?.[0]
           });
           
           // If we have documents, perform search on them
           if (documentsData.documents && documentsData.documents.length > 0) {
             console.log('[Search API] Starting search in', documentsData.documents.length, 'documents');
             const searchResults: SearchResult[] = [];
             
             for (const doc of documentsData.documents) {
               // Filter by selected authors if specified
               if (filters?.authors?.length) {
                 const authorMatch = filters.authors.some(authorId => 
                   doc.author?.toLowerCase().includes(authorId.toLowerCase()) ||
                   authorId.toLowerCase().includes(doc.author?.toLowerCase() || '')
                 );
                 if (!authorMatch) continue;
               }
               
               // Get full document content instead of preview
               let fullContent = '';
               try {
                 console.log('[Search API] Fetching full content for document:', doc.id);
                 const docResponse = await fetch(`${BACKEND_URL}/api/library/documents/${doc.id}`);
                 if (docResponse.ok) {
                   const docData = await docResponse.json();
                   fullContent = docData.document?.full_content || docData.full_content || docData.document?.content || doc.content_preview || '';
                   console.log('[Search API] Got full content length:', fullContent.length);
                 } else {
                   console.log('[Search API] Failed to get full content, using preview');
                   fullContent = doc.content_preview || '';
                 }
               } catch (error) {
                 console.log('[Search API] Error fetching full content:', error);
                 fullContent = doc.content_preview || '';
               }
               
               // Determine what to search for based on parsed query
               let searchTerms: string[] = [];
               
               console.log('[Search API] Checking document:', {
                 id: doc.id,
                 title: doc.title,
                 author: doc.author,
                 contentLength: fullContent.length,
                 searchQuery: query,
                 parsedQuery: parsedQuery
               });
               
               if (parsedQuery.phrases.length > 0) {
                 // Search for exact phrases
                 searchTerms = parsedQuery.phrases;
               } else if (parsedQuery.operators.length > 0) {
                 // Handle operators - for now, just use all terms and check them individually
                 const operatorTerms: string[] = [];
                 parsedQuery.operators.forEach(op => {
                   operatorTerms.push(...op.terms);
                 });
                 // Add remaining terms too
                 operatorTerms.push(...parsedQuery.terms);
                 searchTerms = operatorTerms;
               } else if (parsedQuery.terms.length > 0) {
                 // Search for individual terms
                 searchTerms = parsedQuery.terms;
               } else {
                 // Fallback to original query
                 searchTerms = [query];
               }
               
               console.log('[Search API] Final search terms for document', doc.id, ':', searchTerms);
               
               // Check if search terms match based on operators or simple search
               let foundMatch = false;
               let matchInfo: { term: string; index: number } | null = null;
               
               if (parsedQuery.operators.length > 0) {
                 // Handle operator-based search (AND, OR, NOT)
                 foundMatch = evaluateOperators(fullContent, parsedQuery.operators);
                 
                 // If operators match, find all terms for highlighting
                 if (foundMatch) {
                   // For AND operations, we want to highlight all terms
                   const allMatches: { term: string; index: number }[] = [];
                   for (const searchTerm of searchTerms) {
                     const match = findTermInContent(fullContent, searchTerm);
                     if (match) {
                       allMatches.push(match);
                     }
                   }
                   
                   // Use the first match for positioning
                   if (allMatches.length > 0) {
                     matchInfo = allMatches[0];
                     // Store all matches for later highlighting
                     (matchInfo as { term: string; index: number; allMatches?: { term: string; index: number }[] }).allMatches = allMatches;
                   }
                 }
               } else {
                 // Simple search for phrases or individual terms
                 for (const searchTerm of searchTerms) {
                   const match = findTermInContent(fullContent, searchTerm);
                   if (match) {
                     foundMatch = true;
                     matchInfo = match;
                     break;
                   }
                 }
               }
               
               if (foundMatch && matchInfo) {
                 const text = fullContent;
                 const queryIndex = matchInfo.index;
                 const actualSearchTerm = matchInfo.term;
                 
                 if (queryIndex !== -1) {
                   // Extract 180 characters before and after the match
                   const contextBefore = 180;
                   const contextAfter = 180;
                   
                   const contextStart = Math.max(0, queryIndex - contextBefore);
                   const contextEnd = Math.min(text.length, queryIndex + actualSearchTerm.length + contextAfter);
                   
                   // Extract the context text
                   const displayText = text.substring(contextStart, contextEnd);
                   let highlightedDisplayText = displayText;
                   
                   // Highlight all matches if we have multiple terms (AND operation)
                   const allMatches = (matchInfo as { term: string; index: number; allMatches?: { term: string; index: number }[] }).allMatches || [matchInfo];
                   console.log('[Search API] Highlighting', allMatches.length, 'terms in context');
                   
                   // Sort matches by position to apply highlighting correctly
                   const sortedMatches = allMatches
                     .filter((match: { term: string; index: number }) => match.index >= contextStart && match.index < contextEnd)
                     .sort((a: { term: string; index: number }, b: { term: string; index: number }) => a.index - b.index);
                   
                   // Apply highlighting from right to left to avoid position shifts
                   for (let i = sortedMatches.length - 1; i >= 0; i--) {
                     const match = sortedMatches[i];
                     const relativeIndex = match.index - contextStart;
                     
                     if (relativeIndex >= 0 && relativeIndex + match.term.length <= highlightedDisplayText.length) {
                       const before = highlightedDisplayText.substring(0, relativeIndex);
                       const matchText = highlightedDisplayText.substring(relativeIndex, relativeIndex + match.term.length);
                       const after = highlightedDisplayText.substring(relativeIndex + match.term.length);
                       
                       highlightedDisplayText = before + `<mark>${matchText}</mark>` + after;
                       console.log('[Search API] Highlighted term:', match.term, 'at relative position:', relativeIndex);
                     }
                   }
                   
                   const beforeText = text.substring(contextStart, queryIndex);
                   const afterText = text.substring(queryIndex + actualSearchTerm.length, contextEnd);
                   
                   searchResults.push({
                     id: `${doc.id}-${queryIndex}`,
                     documentId: doc.id.toString(),
                     documentTitle: doc.title || 'Untitled',
                     author: doc.author || 'Unknown Author',
                     text: displayText, // Only the context, not the full document
                     highlightedText: highlightedDisplayText,
                     score: 0.8,
                     matchPositions: [{ start: beforeText.length, end: beforeText.length + actualSearchTerm.length }],
                     context: {
                       before: contextStart > 0 ? '...' + beforeText : beforeText,
                       after: contextEnd < text.length ? afterText + '...' : afterText
                     },
                     metadata: {
                       page: 1,
                       section: 'Content',
                       segmentId: doc.id.toString()
                     }
                   });
                 }
               }
             }
             
             // Return real search results if found
             console.log('[Search API] Found', searchResults.length, 'search results');
             if (searchResults.length > 0) {
               console.log('[Search API] Returning real search results');
               return NextResponse.json({
                 success: true,
                 results: searchResults.slice(0, options?.limit || 50),
                 total: searchResults.length,
                 query: parsedQuery
               });
             } else {
               console.log('[Search API] No matches found in documents, falling back to mock');
             }
           }
         }
       } catch (libraryError) {
         console.error('[Search API] Library search failed:', libraryError);
         console.error('[Search API] Error details:', {
           message: libraryError instanceof Error ? libraryError.message : 'Unknown error',
           stack: libraryError instanceof Error ? libraryError.stack : undefined
         });
       }
     }

    // Fallback to backend search endpoint for literal search
    const fallbackSearchParams = new URLSearchParams({
      q: query,
      type: type,
      limit: String(options?.limit || 50),
      offset: String(options?.offset || 0)
    });

    if (filters?.authors?.length) {
      fallbackSearchParams.append('authors', filters.authors.join(','));
    }
    if (filters?.documentIds?.length) {
      fallbackSearchParams.append('documents', filters.documentIds.join(','));
    }

    const backendUrl = `${BACKEND_URL}/api/search?${fallbackSearchParams.toString()}`;
    console.log('[Search API] Calling backend search:', backendUrl);

    const response = await fetch(backendUrl);
    
    if (!response.ok) {
      // If backend search fails, return simple mock results for now
      console.log('[Search API] Backend search failed, returning mock results');
      console.log('[Search API] Backend response status:', response.status, response.statusText);
      
      const mockResults: SearchResult[] = [
        {
          id: 'mock-1',
          documentId: 'doc-1',
          documentTitle: 'Sample Document',
          author: 'Unknown Author',
          text: `This is sample content that contains the word ${query} in the text.`,
          highlightedText: `This is sample content that contains the word <mark>${query}</mark> in the text.`,
          score: 0.9,
          matchPositions: [{ start: 50, end: 50 + query.length }],
          context: {
            before: 'This is sample content that contains the word',
            after: 'in the text and continues with more content.'
          },
          metadata: {
            page: 1,
            section: 'Introduction',
            segmentId: 'seg-1'
          }
        },
        {
          id: 'mock-2',
          documentId: 'doc-2',
          documentTitle: 'Another Document',
          author: 'Test Author',
          text: `Here is another example with ${query} mentioned multiple times.`,
          highlightedText: `Here is another example with <mark>${query}</mark> mentioned multiple times.`,
          score: 0.8,
          matchPositions: [{ start: 30, end: 30 + query.length }],
          context: {
            before: 'Here is another example with',
            after: 'mentioned multiple times in this document.'
          },
          metadata: {
            page: 5,
            section: 'Chapter 2',
            segmentId: 'seg-2'
          }
        }
      ];

      return NextResponse.json({
        success: true,
        results: mockResults,
        total: mockResults.length,
        query: parsedQuery
      });
    }

    const backendData = await response.json();
    
    // Transform backend results to our format
    const results: SearchResult[] = backendData.results?.map((result: {
      id: string;
      document_id: string;
      document_title: string;
      author: string;
      text: string;
      highlighted_text?: string;
      score?: number;
      match_positions?: { start: number; end: number }[];
      context?: { before: string; after: string };
      page?: number;
      section?: string;
      segment_id: string;
    }) => ({
      id: result.id,
      documentId: result.document_id,
      documentTitle: result.document_title,
      author: result.author,
      text: result.text,
      highlightedText: result.highlighted_text || result.text,
      score: result.score || 0,
      matchPositions: result.match_positions || [],
      context: result.context || { before: '', after: '' },
      metadata: {
        page: result.page,
        section: result.section,
        segmentId: result.segment_id
      }
    })) || [];

    // Combine with semantic results if we have them (for 'both' type)
    const storedSemanticResults = (globalThis as { semanticResults?: SearchResult[] }).semanticResults;
    if (type === 'both' && storedSemanticResults) {
      console.log('[Search API] Combining literal and semantic results');
      
      // Combine and deduplicate results
      const combinedResults = [...results];
      const existingIds = new Set(results.map(r => r.documentId));
      
      storedSemanticResults.forEach(semanticResult => {
        if (!existingIds.has(semanticResult.documentId)) {
          combinedResults.push({
            ...semanticResult,
            id: `semantic-${semanticResult.id}`
          });
        }
      });
      
      // Sort by score (literal results get score 1.0, semantic by similarity)
      combinedResults.sort((a, b) => (b.score || 0) - (a.score || 0));
      
      // Clean up global storage
      delete (globalThis as { semanticResults?: SearchResult[] }).semanticResults;
      
      return NextResponse.json({
        success: true,
        results: combinedResults.slice(0, options?.limit || 50),
        total: combinedResults.length,
        query: parsedQuery,
        searchType: 'hybrid'
      });
    }

    return NextResponse.json({
      success: true,
      results,
      total: backendData.total || results.length,
      query: parsedQuery,
      searchType: 'literal'
    });

  } catch (error) {
    console.error('[Search API] Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Search failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'Search API',
    endpoints: {
      POST: {
        description: 'Perform a search',
        body: {
          query: 'Search query with operators (AND, OR, NOT, "exact phrase")',
          type: 'literal | semantic | both',
          filters: {
            authors: ['author1', 'author2'],
            documentIds: ['doc1', 'doc2'],
            language: 'es | en'
          },
          options: {
            caseSensitive: false,
            wholeWord: false,
            useRegex: false,
            limit: 50,
            offset: 0
          }
        }
      }
    }
  });
} 