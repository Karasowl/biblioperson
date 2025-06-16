import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '20')
    const search = searchParams.get('search') || ''
    const authorId = searchParams.get('authorId')
    const language = searchParams.get('language')
    const genre = searchParams.get('genre')
    const userId = searchParams.get('userId') || 'temp-user-id' // TODO: Get from session

    const skip = (page - 1) * limit

    // Build where clause
    const where: any = {
      uploadedById: userId,
    }

    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { author: { name: { contains: search, mode: 'insensitive' } } },
        { genre: { contains: search, mode: 'insensitive' } },
      ]
    }

    if (authorId) {
      where.authorId = authorId
    }

    if (language) {
      where.language = language
    }

    if (genre) {
      where.genre = genre
    }

    // Get documents with pagination
    const [documents, total] = await Promise.all([
      prisma.document.findMany({
        where,
        include: {
          author: true,
          favorites: {
            where: { userId },
          },
          readingProgress: {
            where: { userId },
          },
          _count: {
            select: {
              annotations: true,
              segments: true,
            }
          }
        },
        orderBy: {
          createdAt: 'desc'
        },
        skip,
        take: limit,
      }),
      prisma.document.count({ where })
    ])

    // Transform data for frontend
    const transformedDocuments = documents.map(doc => ({
      id: doc.id,
      title: doc.title,
      author: {
        id: doc.author.id,
        name: doc.author.name,
        specialty: doc.author.specialty,
      },
      fileType: doc.fileType,
      fileSize: doc.fileSize,
      language: doc.language,
      genre: doc.genre,
      summary: doc.summary,
      wordCount: doc.wordCount,
      pageCount: doc.pageCount,
      coverColor: doc.coverColor,
      tags: doc.tags,
      isProcessed: doc.isProcessed,
      isFavorite: doc.favorites.length > 0,
      readingProgress: doc.readingProgress[0] || null,
      annotationCount: doc._count.annotations,
      segmentCount: doc._count.segments,
      createdAt: doc.createdAt,
      updatedAt: doc.updatedAt,
    }))

    return NextResponse.json({
      documents: transformedDocuments,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
        hasNext: page * limit < total,
        hasPrev: page > 1,
      }
    })

  } catch (error) {
    console.error('Error fetching documents:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { title, authorName, language = 'es', genre, tags = [] } = body

    if (!title || !authorName) {
      return NextResponse.json(
        { error: 'Title and author name are required' },
        { status: 400 }
      )
    }

    // Find or create author
    const author = await prisma.author.upsert({
      where: { name: authorName },
      update: {},
      create: {
        name: authorName,
        description: `Autor de ${title}`,
      }
    })

    // Create document
    const document = await prisma.document.create({
      data: {
        title,
        originalPath: '', // Will be set when file is uploaded
        fileType: 'manual',
        fileSize: 0,
        language,
        genre,
        tags,
        authorId: author.id,
        uploadedById: 'temp-user-id', // TODO: Get from session
        pageCount: 0,
      },
      include: {
        author: true,
      }
    })

    return NextResponse.json({
      success: true,
      document: {
        id: document.id,
        title: document.title,
        author: document.author.name,
        language: document.language,
        genre: document.genre,
        tags: document.tags,
      }
    })

  } catch (error) {
    console.error('Error creating document:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 