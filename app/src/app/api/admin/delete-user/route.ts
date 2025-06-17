import { NextRequest, NextResponse } from 'next/server';
import { createSupabaseBrowserClient } from '@/lib/supabase';

export async function DELETE(request: NextRequest) {
  try {
    const { email, userId } = await request.json();
    
    if (!email && !userId) {
      return NextResponse.json({ 
        error: 'Email or userId is required' 
      }, { status: 400 });
    }

    const supabase = createSupabaseBrowserClient();

    // First, find the user if we only have email
    let userIdToDelete = userId;
    
    if (!userIdToDelete && email) {
      const { data: user } = await supabase
        .from('users')
        .select('id')
        .eq('email', email)
        .single();
      
      if (user) {
        userIdToDelete = user.id;
      }
    }

    if (!userIdToDelete) {
      return NextResponse.json({ 
        error: 'User not found' 
      }, { status: 404 });
    }

    // Delete from custom tables first (in dependency order)
    const { error: configError } = await supabase
      .from('user_processing_configs')
      .delete()
      .eq('user_id', userIdToDelete);

    const { error: prefsError } = await supabase
      .from('user_preferences')
      .delete()
      .eq('user_id', userIdToDelete);

    const { error: userError } = await supabase
      .from('users')
      .delete()
      .eq('id', userIdToDelete);

    // Try to delete from auth.users using RPC function
    // (this requires that you've configured an RPC function in Supabase)
    const { error: authError } = await supabase.rpc('delete_auth_user', {
      user_id: userIdToDelete
    });

    const errors = [configError, prefsError, userError, authError].filter(Boolean);
    
    if (errors.length > 0) {
      console.warn('Some errors during deletion:', errors);
    }

    return NextResponse.json({ 
      success: true,
      message: `User deleted (ID: ${userIdToDelete})`,
      errors: errors.length > 0 ? errors : undefined
    });

  } catch (error) {
    console.error('Error deleting user:', error);
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

// GET endpoint to list users (useful for debugging)
export async function GET() {
  try {
    const supabase = createSupabaseBrowserClient();
    
    const { data: users, error } = await supabase
      .from('users')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ 
      users: users,
      count: users.length 
    });

  } catch (error) {
    console.error('Error listing users:', error);
    return NextResponse.json({ 
      error: 'Internal server error' 
    }, { status: 500 });
  }
} 