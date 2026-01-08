import sqlite3
from datetime import datetime
import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

print('\n' + '='*70)
print('              DATABASE CONTENTS (app.db)'.center(70))
print('='*70 + '\n')

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"📊 Tables: {[t[0] for t in tables]}\n")

print('='*70)
print('👥 USERS TABLE'.center(70))
print('='*70 + '\n')

# Show all users
cursor.execute('SELECT id, username, email, password_hash, created_at FROM users')
users = cursor.fetchall()

if users:
    for user in users:
        print(f'🆔 ID:            {user[0]}')
        print(f'👤 Username:      {user[1]}')
        print(f'📧 Email:         {user[2]}')
        print(f'🔒 Password Hash: {user[3][:60]}...')
        print(f'📅 Created At:    {user[4]}')
        print('-'*70)
    print(f'\n📈 Total Users: {len(users)}')
else:
    print('No users found in database.\n')

print('='*70 + '\n')

# Check if inventory_items table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_items'")
if cursor.fetchone():
    print('='*70)
    print('📦 INVENTORY ITEMS TABLE'.center(70))
    print('='*70 + '\n')

    # Show all inventory items
    cursor.execute('''
        SELECT i.id, i.name, i.quantity, i.category, i.user_id, u.username, i.created_at 
        FROM inventory_items i
        LEFT JOIN users u ON i.user_id = u.id
        ORDER BY i.user_id, i.created_at DESC
    ''')
    items = cursor.fetchall()

    if items:
        current_user_id = None
        for item in items:
            if current_user_id != item[4]:
                current_user_id = item[4]
                print(f'\n👤 User: {item[5]} (ID: {item[4]})')
                print('-'*70)
            
            print(f'  📦 Item ID:      {item[0]}')
            print(f'  🏷️  Name:         {item[1]}')
            print(f'  📊 Quantity:     {item[2]}')
            print(f'  🗂️  Category:     {item[3] or "N/A"}')
            print(f'  📅 Added:        {item[6]}')
            print('-'*70)
        
        print(f'\n📈 Total Inventory Items: {len(items)}')
    else:
        print('No inventory items found in database.\n')
    
    print('='*70 + '\n')

# Check if inventory table exists (LangGraph/DatabaseHelper - Active Table)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
if cursor.fetchone():
    print('='*70)
    print('📦 INVENTORY TABLE (Active - LangGraph/DatabaseHelper)'.center(70))
    print('='*70 + '\n')

    cursor.execute('''
        SELECT i.id, i.name, i.quantity, i.unit, i.user_id, u.username, u.email, i.created_at, i.updated_at
        FROM inventory i
        LEFT JOIN users u ON i.user_id = u.id
        ORDER BY i.user_id, i.updated_at DESC
    ''')
    items = cursor.fetchall()

    if items:
        current_user_id = None
        for item in items:
            if current_user_id != item[4]:
                current_user_id = item[4]
                print(f'\n👤 User: {item[5]} ({item[6]}) - ID: {item[4]}')
                print('-'*70)
            
            print(f'  📦 Item ID:      {item[0]}')
            print(f'  🏷️  Name:         {item[1]}')
            print(f'  📊 Quantity:     {item[2]} {item[3]}')
            print(f'  📅 Created:      {item[7]}')
            print(f'  🔄 Updated:      {item[8]}')
            print('-'*70)
        
        print(f'\n📈 Total Inventory Items: {len(items)}')
    else:
        print('No inventory items found in database.\n')
    
    print('='*70 + '\n')

# Check if shopping_list table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shopping_list'")
if cursor.fetchone():
    print('='*70)
    print('🛒 SHOPPING LIST TABLE'.center(70))
    print('='*70 + '\n')

    cursor.execute('''
        SELECT s.id, s.name, s.quantity, s.checked, s.user_id, u.username, u.email, s.created_at, s.updated_at
        FROM shopping_list s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.user_id, s.checked ASC, s.created_at DESC
    ''')
    items = cursor.fetchall()

    if items:
        current_user_id = None
        for item in items:
            if current_user_id != item[4]:
                current_user_id = item[4]
                print(f'\n👤 User: {item[5]} ({item[6]}) - ID: {item[4]}')
                print('-'*70)
            
            checked_icon = '✅' if item[3] == 1 else '⬜'
            print(f'  {checked_icon} Item ID:     {item[0]}')
            print(f'  🏷️  Name:         {item[1]}')
            print(f'  📊 Quantity:     {item[2]}')
            print(f'  ✓  Checked:      {"Yes" if item[3] == 1 else "No"}')
            print(f'  📅 Created:      {item[7]}')
            print(f'  🔄 Updated:      {item[8]}')
            print('-'*70)
        
        print(f'\n📈 Total Shopping List Items: {len(items)}')
        checked_count = sum(1 for item in items if item[3] == 1)
        unchecked_count = len(items) - checked_count
        print(f'✅ Checked: {checked_count} | ⬜ Unchecked: {unchecked_count}')
    else:
        print('No shopping list items found in database.\n')
    
    print('='*70 + '\n')

conn.close()
print("\n✅ Database view complete!\n")

