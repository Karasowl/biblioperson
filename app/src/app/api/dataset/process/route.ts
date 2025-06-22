import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { join } from 'path';

interface ProcessingConfig {
  inputType: 'file' | 'folder';
  selectedFiles?: File[];
  selectedFolder: string;
  recursiveRead: boolean;
  profile: string;
  forceLanguage: boolean;
  language: string;
  forceAuthor: boolean;
  author: string;
  title: string;
  tags: string;
  detailedMode: boolean;
  parallelProcessing: boolean;
  showProcessingTimes: boolean;
  forceContentType: boolean;
  contentType: string;
  workers: number;
  outputFormat: string;
  unifyOutput: boolean;
  encoding: string;
  jsonConfig: {
    textPaths: string;
    rootArrayPath: string;
    treatAsSingleObject: boolean;
    idField: string;
    dateField: string;
    minTextLength: { enabled: boolean; value: number };
    maxTextLength: { enabled: boolean; value: number };
    filterRules: Array<{
      id: string;
      field: string;
      operator: string;
      value: string;
      caseSensitive?: boolean;
      negate?: boolean;
    }>;
  };
  enableOCR: boolean;
  enableAuthorDetection: boolean;
  enableDeduplication: boolean;
}

// POST - Iniciar procesamiento de dataset
export async function POST(request: NextRequest) {
  try {
    const config: ProcessingConfig = await request.json();

    // Validar configuración
    if (config.inputType === 'file' && !config.selectedFiles) {
      return NextResponse.json(
        { error: 'No files selected' },
        { status: 400 }
      );
    }

    if (config.inputType === 'folder' && !config.selectedFolder) {
      return NextResponse.json(
        { error: 'No folder selected' },
        { status: 400 }
      );
    }

    // Preparar argumentos para el script de Python
    const pythonScript = join(process.cwd(), 'dataset', 'scripts', 'process_file.py');
    const args = [pythonScript];

    // Agregar argumentos según la configuración
    if (config.inputType === 'folder') {
      args.push('--input', config.selectedFolder);
    }

    args.push('--profile', config.profile === 'automatico' ? 'auto' : config.profile);
    
    if (config.forceLanguage) {
      args.push('--language', config.language);
    }
    
    if (config.forceAuthor) {
      args.push('--author', config.author);
    }

    if (config.detailedMode) {
      args.push('--verbose');
    }

    if (config.parallelProcessing) {
      args.push('--parallel', '--workers', config.workers.toString());
    }

    if (config.enableOCR) {
      args.push('--ocr');
    }

    if (config.enableAuthorDetection) {
      args.push('--detect-author');
    }

    if (config.enableDeduplication) {
      args.push('--dedup');
    }

    args.push('--output-format', config.outputFormat);
    args.push('--encoding', config.encoding);

    // Configurar directorio de salida temporal
    const outputDir = join(process.cwd(), 'temp', `processing_${Date.now()}`);
    args.push('--output', outputDir);

    // Ejecutar el proceso de Python
    return new Promise<Response>((resolve) => {
      const pythonProcess = spawn('python', args, {
        cwd: process.cwd(),
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let output = '';
      let errorOutput = '';
      let isCompleted = false;

      // Capturar salida estándar
      pythonProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        output += chunk;
        console.log('Python output:', chunk);
      });

      // Capturar errores
      pythonProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        errorOutput += chunk;
        console.error('Python error:', chunk);
      });

      // Manejar finalización del proceso
      pythonProcess.on('close', (code) => {
        isCompleted = true;
        if (code === 0) {
          resolve(NextResponse.json({
            success: true,
            message: 'Processing completed successfully',
            output: output,
            outputDir: outputDir
          }));
        } else {
          resolve(NextResponse.json({
            success: false,
            error: 'Processing failed',
            output: output,
            errorOutput: errorOutput,
            exitCode: code
          }, { status: 500 }));
        }
      });

      // Manejar errores del proceso
      pythonProcess.on('error', (error) => {
        if (!isCompleted) {
          isCompleted = true;
          resolve(NextResponse.json({
            success: false,
            error: 'Failed to start Python process',
            details: error.message
          }, { status: 500 }));
        }
      });

      // Timeout de 5 minutos
      setTimeout(() => {
        if (!isCompleted) {
          pythonProcess.kill();
          resolve(NextResponse.json({
            success: false,
            error: 'Processing timeout (5 minutes)',
            output: output,
            errorOutput: errorOutput
          }, { status: 408 }));
        }
      }, 300000); // 5 minutos
    });

  } catch (error) {
    console.error('Dataset processing error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// GET - Obtener estado del procesamiento
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const processId = searchParams.get('processId');

  if (!processId) {
    return NextResponse.json({
      status: 'idle',
      message: 'No process running'
    });
  }

  // TODO: Implementar seguimiento de procesos activos
  return NextResponse.json({
    status: 'processing',
    message: 'Process status tracking not implemented yet'
  });
} 