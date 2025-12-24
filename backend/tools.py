"""
Agent Tools for Pharmacy Assistant

This module defines all the tools (functions) that the AI agent can use
to interact with the pharmacy database.
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any

# Get the database path relative to this file
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
DATABASE_PATH = os.path.join(PROJECT_DIR, 'database', 'pharmacy.db')

def get_db_connection():
    """Get a connection to the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_medication_by_name(medication_name: str) -> Dict[str, Any]:
    """
    Search for a medication by name.

    Args:
        medication_name: The name of the medication to search for

    Returns:
        Dictionary containing medication details or error message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Search with LIKE for partial matches
        cursor.execute('''
            SELECT * FROM medications
            WHERE name LIKE ? OR active_ingredient LIKE ?
        ''', (f'%{medication_name}%', f'%{medication_name}%'))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'success': True,
                'medication': {
                    'id': result['id'],
                    'name': result['name'],
                    'active_ingredient': result['active_ingredient'],
                    'dosage': result['dosage'],
                    'requires_prescription': bool(result['requires_prescription']),
                    'in_stock': bool(result['in_stock']),
                    'usage_instructions': result['usage_instructions'],
                    'side_effects': result['side_effects'],
                    'description': result['description'],
                    'category': result['category']
                }
            }
        else:
            return {
                'success': False,
                'error': f'Medication "{medication_name}" not found. Please check spelling or try another name.',
                'suggestion': 'Try searching by active ingredient or category.'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Search error: {str(e)}'
        }

def check_medication_stock(medication_name: str) -> Dict[str, Any]:
    """
    Check if a medication is in stock.

    Args:
        medication_name: The name of the medication

    Returns:
        Dictionary with stock availability information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT name, in_stock FROM medications
            WHERE name LIKE ?
        ''', (f'%{medication_name}%',))

        result = cursor.fetchone()
        conn.close()

        if result:
            in_stock = bool(result['in_stock'])

            return {
                'success': True,
                'medication_name': result['name'],
                'in_stock': in_stock,
                'message': f'Yes, {result["name"]} is in stock.' if in_stock else f'No, {result["name"]} is out of stock.'
            }
        else:
            return {
                'success': False,
                'error': f'Medication "{medication_name}" not found.'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error checking stock: {str(e)}'
        }

def search_medications(filter_type: str = "all", query: str = "") -> Dict[str, Any]:
    """
    Search for medications with various filters.

    Args:
        filter_type: Type of search - "ingredient", "category", or "all"
        query: Search query (not needed for "all")

    Returns:
        Dictionary with list of medications
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if filter_type == "ingredient":
            cursor.execute('''
                SELECT name, active_ingredient, dosage, requires_prescription, in_stock
                FROM medications
                WHERE active_ingredient LIKE ?
            ''', (f'%{query}%',))
        elif filter_type == "category":
            cursor.execute('''
                SELECT name, active_ingredient, dosage, requires_prescription, in_stock
                FROM medications
                WHERE category LIKE ?
            ''', (f'%{query}%',))
        else:  # "all"
            cursor.execute('''
                SELECT name, active_ingredient, dosage, requires_prescription, in_stock
                FROM medications
                ORDER BY name
            ''')

        results = cursor.fetchall()
        conn.close()

        if results:
            medications = [
                {
                    'name': row['name'],
                    'active_ingredient': row['active_ingredient'],
                    'dosage': row['dosage'],
                    'requires_prescription': bool(row['requires_prescription']),
                    'in_stock': bool(row['in_stock'])
                }
                for row in results
            ]

            return {
                'success': True,
                'filter_type': filter_type,
                'query': query if query else "all medications",
                'count': len(medications),
                'medications': medications
            }
        else:
            return {
                'success': False,
                'error': f'No medications found for {filter_type}: "{query}"'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error searching medications: {str(e)}'
        }

def check_prescription(user_id: int, medication_name: str) -> Dict[str, Any]:
    """
    Check prescription status for a user and medication.
    This includes: Does the medication require a prescription? Does the user have one?

    Args:
        user_id: The user's ID
        medication_name: The name of the medication

    Returns:
        Dictionary with prescription requirement and user prescription status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user info
        cursor.execute('SELECT name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return {
                'success': False,
                'error': f'User #{user_id} not found in the system.'
            }

        user_name = user['name']

        # Find medication
        cursor.execute('''
            SELECT id, name, requires_prescription
            FROM medications
            WHERE name LIKE ?
        ''', (f'%{medication_name}%',))

        medication = cursor.fetchone()

        if not medication:
            conn.close()
            return {
                'success': False,
                'error': f'Medication "{medication_name}" not found in the system.'
            }

        medication_id = medication['id']
        medication_full_name = medication['name']
        requires_prescription = bool(medication['requires_prescription'])

        # Check if user has prescription
        cursor.execute('''
            SELECT p.*, m.name as medication_name
            FROM prescriptions p
            JOIN medications m ON p.medication_id = m.id
            WHERE p.user_id = ? AND p.medication_id = ?
            ORDER BY p.prescription_date DESC
            LIMIT 1
        ''', (user_id, medication_id))

        prescription = cursor.fetchone()
        conn.close()

        if prescription:
            return {
                'success': True,
                'user_name': user_name,
                'medication_name': medication_full_name,
                'has_prescription': True,
                'requires_prescription': requires_prescription,
                'message': f'Yes, {user_name} has a prescription for {medication_full_name}.'
            }
        else:
            if requires_prescription:
                return {
                    'success': True,
                    'user_name': user_name,
                    'medication_name': medication_full_name,
                    'has_prescription': False,
                    'requires_prescription': True,
                    'message': f'{user_name} does not have a prescription for {medication_full_name}. This medication requires a doctor\'s prescription. Please consult a doctor to get a prescription.'
                }
            else:
                return {
                    'success': True,
                    'user_name': user_name,
                    'medication_name': medication_full_name,
                    'has_prescription': False,
                    'requires_prescription': False,
                    'message': f'{medication_full_name} is an over-the-counter medication, so {user_name} can purchase it without a prescription.'
                }

    except Exception as e:
        return {
            'success': False,
            'error': f'Error checking prescription: {str(e)}'
        }

# Tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_medication_by_name",
            "description": "Search for a specific medication by name. Returns detailed information including active ingredient, dosage, usage instructions, side effects, and prescription requirements. Use this when user asks about a specific medication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "The name of the medication to search for"
                    }
                },
                "required": ["medication_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_medications",
            "description": "Search for medications with various filters: by active ingredient, by category (pain_relief, antibiotic, allergy, cholesterol), or get all medications. Use this for broader searches or when user wants to explore options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_type": {
                        "type": "string",
                        "enum": ["ingredient", "category", "all"],
                        "description": "Type of search: 'ingredient' to search by active ingredient, 'category' to search by medication category, or 'all' to list all medications"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query - the ingredient name or category name. Not needed when filter_type is 'all'"
                    }
                },
                "required": ["filter_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_medication_stock",
            "description": "Check if a medication is available in stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "The name of the medication to check"
                    }
                },
                "required": ["medication_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_prescription",
            "description": "Check prescription status for a user and medication. This tool checks both: (1) Does this medication require a prescription? (2) Does the user have an active prescription for it? Use when user asks about prescriptions or if they can get a medication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The user's ID (1-10)"
                    },
                    "medication_name": {
                        "type": "string",
                        "description": "The name of the medication to check"
                    }
                },
                "required": ["user_id", "medication_name"]
            }
        }
    }
]

# Map function names to actual functions
TOOL_FUNCTIONS = {
    "get_medication_by_name": get_medication_by_name,
    "search_medications": search_medications,
    "check_medication_stock": check_medication_stock,
    "check_prescription": check_prescription
}
