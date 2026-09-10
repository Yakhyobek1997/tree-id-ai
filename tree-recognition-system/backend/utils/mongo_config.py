"""
MongoDB Configuration
Manages MongoDB connection settings and utilities
"""
import os
from typing import Optional


class MongoConfig:
    """MongoDB connection configuration"""
    
    # Default settings
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 27017
    DEFAULT_DB_NAME = 'tree_recognition'
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        connection_string: Optional[str] = None
    ):
        """
        Initialize MongoDB configuration
        
        Args:
            host: MongoDB host (default: localhost)
            port: MongoDB port (default: 27017)
            username: MongoDB username (optional)
            password: MongoDB password (optional)
            database: Database name (default: tree_recognition)
            connection_string: Full connection string (overrides other params)
        """
        # Load from environment variables if not provided
        self.host = host or os.getenv('MONGO_HOST', self.DEFAULT_HOST)
        self.port = port or int(os.getenv('MONGO_PORT', self.DEFAULT_PORT))
        self.username = username or os.getenv('MONGO_USERNAME')
        self.password = password or os.getenv('MONGO_PASSWORD')
        self.database = database or os.getenv('MONGO_DATABASE', self.DEFAULT_DB_NAME)
        self._connection_string = connection_string or os.getenv('MONGO_CONNECTION_STRING')
    
    @property
    def connection_string(self) -> str:
        """
        Generate MongoDB connection string
        
        Returns:
            MongoDB connection URI
        """
        # Use custom connection string if provided
        if self._connection_string:
            return self._connection_string
        
        # Build connection string
        if self.username and self.password:
            # Authenticated connection
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
        else:
            # Local connection without authentication
            return f"mongodb://{self.host}:{self.port}/"
    
    def get_database_manager(self):
        """
        Create and return DatabaseManager instance with MongoDB
        
        Returns:
            DatabaseManager instance configured for MongoDB
        """
        from backend.database.db_manager import DatabaseManager
        return DatabaseManager(
            db_type='mongodb',
            connection_string=self.connection_string,
            database_name=self.database
        )
    
    @classmethod
    def from_env(cls) -> 'MongoConfig':
        """
        Create configuration from environment variables
        
        Environment variables:
            - MONGO_HOST: MongoDB host
            - MONGO_PORT: MongoDB port
            - MONGO_USERNAME: MongoDB username (optional)
            - MONGO_PASSWORD: MongoDB password (optional)
            - MONGO_DATABASE: Database name
            - MONGO_CONNECTION_STRING: Full connection string (overrides others)
        
        Returns:
            MongoConfig instance
        """
        return cls()
    
    @classmethod
    def for_local(cls, database: str = None) -> 'MongoConfig':
        """
        Create configuration for local MongoDB instance
        
        Args:
            database: Database name (default: tree_recognition)
        
        Returns:
            MongoConfig instance for local connection
        """
        return cls(
            host='localhost',
            port=27017,
            database=database or cls.DEFAULT_DB_NAME
        )
    
    @classmethod
    def for_atlas(
        cls,
        cluster_url: str,
        username: str,
        password: str,
        database: str = None
    ) -> 'MongoConfig':
        """
        Create configuration for MongoDB Atlas
        
        Args:
            cluster_url: MongoDB Atlas cluster URL (e.g., cluster0.xxxxx.mongodb.net)
            username: Atlas username
            password: Atlas password
            database: Database name (default: tree_recognition)
        
        Returns:
            MongoConfig instance for Atlas connection
        """
        connection_string = (
            f"mongodb+srv://{username}:{password}@{cluster_url}/"
            f"{database or cls.DEFAULT_DB_NAME}?retryWrites=true&w=majority"
        )
        return cls(
            connection_string=connection_string,
            database=database or cls.DEFAULT_DB_NAME
        )
    
    def __str__(self) -> str:
        """String representation (without password)"""
        safe_connection = self.connection_string
        if self.password:
            safe_connection = safe_connection.replace(self.password, '****')
        return f"MongoConfig(database={self.database}, connection={safe_connection})"
    
    def __repr__(self) -> str:
        return self.__str__()


# Example usage configurations
EXAMPLE_CONFIGS = {
    'local': """
# Local MongoDB
from backend.utils.mongo_config import MongoConfig
config = MongoConfig.for_local()
db_manager = config.get_database_manager()
""",
    
    'atlas': """
# MongoDB Atlas
from backend.utils.mongo_config import MongoConfig
config = MongoConfig.for_atlas(
    cluster_url='cluster0.xxxxx.mongodb.net',
    username='your_username',
    password='your_password'
)
db_manager = config.get_database_manager()
""",
    
    'env': """
# From environment variables
# Set environment variables:
# export MONGO_HOST=localhost
# export MONGO_PORT=27017
# export MONGO_DATABASE=tree_recognition

from backend.utils.mongo_config import MongoConfig
config = MongoConfig.from_env()
db_manager = config.get_database_manager()
"""
}


if __name__ == "__main__":
    # Test configurations
    print("=" * 60)
    print("MongoDB Configuration Examples")
    print("=" * 60)
    
    # Local config
    print("\n1. Local MongoDB:")
    local_config = MongoConfig.for_local()
    print(f"   {local_config}")
    
    # Atlas config (example)
    print("\n2. MongoDB Atlas (example):")
    atlas_config = MongoConfig.for_atlas(
        cluster_url='cluster0.xxxxx.mongodb.net',
        username='username',
        password='password'
    )
    print(f"   {atlas_config}")
    
    # Environment config
    print("\n3. From Environment Variables:")
    env_config = MongoConfig.from_env()
    print(f"   {env_config}")
    
    print("\n" + "=" * 60)
    print("Example Usage:")
    print("=" * 60)
    for name, example in EXAMPLE_CONFIGS.items():
        print(f"\n{name.upper()}:")
        print(example)


