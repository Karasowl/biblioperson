import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: documentId } = await params

    if (!documentId) {
      return NextResponse.json(
        { error: 'Document ID is required' },
        { status: 400 }
      )
    }

    // TODO: Add user authentication and authorization
    // const userId = await getUserFromRequest(request)
    const userId = 'temp-user-id'

    // Check if document exists and belongs to user
    const existingDocument = await prisma.document.findFirst({
      where: {
        id: documentId,
        uploadedById: userId,
      }
    })

    if (!existingDocument) {
      return NextResponse.json(
        { error: 'Document not found or you do not have permission to delete it' },
        { status: 404 }
      )
    }

    // Delete related data in order (due to foreign key constraints)
    await prisma.$transaction(async (tx) => {
      // Delete annotations first
      await tx.annotation.deleteMany({
        where: { documentId }
      })

      // Delete reading progress
      await tx.readingProgress.deleteMany({
        where: { documentId }
      })

      // Delete favorites
      await tx.favorite.deleteMany({
        where: { documentId }
      })

      // Delete segments
      await tx.segment.deleteMany({
        where: { documentId }
      })

      // Delete notebooks associated with this document
      await tx.annotationNotebook.deleteMany({
        where: { documentId }
      })

      // Finally delete the document
      await tx.document.delete({
        where: { id: documentId }
      })
    })

    return NextResponse.json({
      success: true,
      message: 'Document deleted successfully'
    })

  } catch (error) {
    console.error('Error deleting document:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: documentId } = await params

    if (!documentId) {
      return NextResponse.json(
        { error: 'Document ID is required' },
        { status: 400 }
      )
    }

    // TODO: Add user authentication
    const userId = 'temp-user-id'

    const document = await prisma.document.findFirst({
      where: {
        id: documentId,
        uploadedById: userId,
      },
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
      }
    })

    if (!document) {
      return NextResponse.json(
        { error: 'Document not found' },
        { status: 404 }
      )
    }

    // Transform data for frontend
    const transformedDocument = {
      id: document.id,
      title: document.title,
      author: {
        id: document.author.id,
        name: document.author.name,
        specialty: document.author.specialty,
      },
      fileType: document.fileType,
      fileSize: document.fileSize,
      language: document.language,
      genre: document.genre,
      summary: document.summary,
      wordCount: document.wordCount,
      pageCount: document.pageCount,
      coverColor: document.coverColor,
      tags: document.tags,
      isProcessed: document.isProcessed,
      isFavorite: document.favorites.length > 0,
      readingProgress: document.readingProgress[0] || null,
      annotationCount: document._count.annotations,
      segmentCount: document._count.segments,
      createdAt: document.createdAt,
      updatedAt: document.updatedAt,
    }

    return NextResponse.json({
      success: true,
      document: transformedDocument
    })

  } catch (error) {
    console.error('Error fetching document:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 