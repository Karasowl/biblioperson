import { NextResponse } from 'next/server';
import { createSupabaseBrowserClient } from '@/lib/supabase';

export async function POST() {
  try {
    const supabase = createSupabaseBrowserClient();
    
    // Create the SQL function to delete users from auth.users
    const createFunctionSQL = `
      CREATE OR REPLACE FUNCTION delete_auth_user(user_id uuid)
      RETURNS void
      LANGUAGE plpgsql
      SECURITY DEFINER
      AS $$
      BEGIN
        DELETE FROM auth.users WHERE id = user_id;
      END;
      $$;
    `;

    const { error } = await supabase.rpc('exec_sql', { 
      sql: createFunctionSQL 
    });

    if (error) {
      console.error('Error creating function:', error);
      return NextResponse.json({ 
        error: 'Could not create function', 
        details: error.message 
      }, { status: 500 });
    }

    return NextResponse.json({ 
      success: true,
      message: 'delete_auth_user function created successfully' 
    });

  } catch (error) {
    console.error('Error setting up delete function:', error);
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
} 