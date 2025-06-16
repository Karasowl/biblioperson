import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { join } from 'path'
import { prisma } from '@/lib/prisma'
import { isValidFileType, generateRandomColor } from '@/lib/utils'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const authorName = formData.get('authorName') as string
    const language = formData.get('language') as string || 'es'
    const autoDetect = formData.get('autoDetect') === 'true'
    
    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      )
    }

    // Validate file type
    if (!isValidFileType(file.name)) {
      return NextResponse.json(
        { error: 'Invalid file type. Supported: PDF, EPUB, TXT, DOCX, MD' },
        { status: 400 }
      )
    }

    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (file.size > maxSize) {
      return NextResponse.json(
        { error: 'File too large. Maximum size is 50MB' },
        { status: 400 }
      )
    }

    // Create uploads directory if it doesn't exist
    const uploadsDir = join(process.cwd(), 'uploads')
    try {
      await mkdir(uploadsDir, { recursive: true })
    } catch (error) {
      // Directory might already exist
    }

    // Generate unique filename
    const timestamp = Date.now()
    const filename = `${timestamp}-${file.name}`
    const filepath = join(uploadsDir, filename)

    // Save file
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filepath, buffer)

    // Find or create author
    let author
    if (authorName) {
      author = await prisma.author.upsert({
        where: { name: authorName },
        update: {},
        create: {
          name: authorName,
          description: `Autor de ${file.name.split('.')[0]}`,
        }
      })
    } else {
      // Create a default "Unknown Author" if auto-detection is disabled
      author = await prisma.author.upsert({
        where: { name: 'Autor Desconocido' },
        update: {},
        create: {
          name: 'Autor Desconocido',
          description: 'Autor no especificado',
        }
      })
    }

    // Create document record
    const document = await prisma.document.create({
      data: {
        title: file.name.split('.')[0], // Remove extension
        originalPath: filepath,
        fileType: file.name.split('.').pop()?.toLowerCase() || 'unknown',
        fileSize: file.size,
        language,
        coverColor: generateRandomColor(),
        authorId: author.id,
        uploadedById: 'temp-user-id', // TODO: Replace with actual user ID from session
        pageCount: 0, // Will be updated after processing
      },
      include: {
        author: true,
      }
    })

    // TODO: Queue document for processing with Python scripts
    // This would involve calling the dataset processing pipeline

    return NextResponse.json({
      success: true,
      document: {
        id: document.id,
        title: document.title,
        author: document.author.name,
        fileType: document.fileType,
        fileSize: document.fileSize,
        language: document.language,
        coverColor: document.coverColor,
      },
      message: 'File uploaded successfully. Processing will begin shortly.'
    })

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { error: 'Internal server error during file upload' },
      { status: 500 }
    )
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'Upload endpoint. Use POST to upload files.',
    supportedTypes: ['PDF', 'EPUB', 'TXT', 'DOCX', 'MD'],
    maxSize: '50MB'
  })
} 