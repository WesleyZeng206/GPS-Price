"""
Database connection and management for MySQL
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import bcrypt

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.database = os.getenv('DB_NAME')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD')
    
    def connect(self) -> bool:
        """
        Establish connection to MySQL database
        Returns True if successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True
            )
            
            if self.connection.is_connected():
                print("Successfully connected to MySQL database")
                return True
                
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")
    
    def create_tables(self) -> bool:
        """
        Create the users table with required fields
        Returns True if successful, False otherwise
        """
        if not self.connection or not self.connection.is_connected():
            print("No database connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_users_table)
            print("Users table created successfully")
            cursor.close()
            return True
            
        except Error as e:
            print(f"Error creating tables: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def create_user(self, username: str, name: str, email: str, password: str) -> bool:
        """
        Create a new user in the database
        Returns True if successful, False otherwise
        """
        if not self.connection or not self.connection.is_connected():
            print("No database connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            hashed_password = self.hash_password(password)
            
            insert_query = """
            INSERT INTO users (username, name, email, password)
            VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (username, name, email, hashed_password))
            print(f"User {username} created successfully")
            cursor.close()
            return True
            
        except Error as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by username
        Returns user data as dictionary or None if not found
        """
        if not self.connection or not self.connection.is_connected():
            print("No database connection")
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            select_query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(select_query, (username,))
            
            user = cursor.fetchone()
            cursor.close()
            return user
            
        except Error as e:
            print(f"Error retrieving user: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Retrieve all users from database
        Returns list of user dictionaries
        """
        if not self.connection or not self.connection.is_connected():
            print("No database connection")
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            select_query = "SELECT id, username, name, email, created_at, updated_at FROM users"
            cursor.execute(select_query)
            
            users = cursor.fetchall()
            cursor.close()
            return users
            
        except Error as e:
            print(f"Error retrieving users: {e}")
            return []
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify user password using bcrypt
        Returns True if password matches, False otherwise
        """
        user = self.get_user_by_username(username)
        if not user:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
    
    def initialize_database(self) -> bool:
        """
        Initialize database connection and create tables
        Returns True if successful, False otherwise
        """
        if self.connect():
            return self.create_tables()
        return False

# Global database instance
db = DatabaseManager()