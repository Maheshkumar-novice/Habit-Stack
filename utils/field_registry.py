"""
Field registry system for dynamic encryption field management
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from database import get_db
import logging


@dataclass
class EncryptableField:
    """Represents a field that can be encrypted"""
    module: str
    field_name: str
    display_name: str
    description: str
    recommended: bool = True
    version_added: str = "1.0"
    
    def __eq__(self, other):
        if not isinstance(other, EncryptableField):
            return False
        return (self.module == other.module and 
                self.field_name == other.field_name)
    
    def __hash__(self):
        return hash((self.module, self.field_name))


class FieldRegistry:
    """Manages registration and discovery of encryptable fields"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fields: List[EncryptableField] = []
        self._register_default_fields()
    
    def _register_default_fields(self):
        """Register all current encryptable fields"""
        default_fields = [
            # Habits module
            EncryptableField(
                module="habits",
                field_name="name", 
                display_name="Habit Names",
                description="Your personal habit titles and goals",
                recommended=True
            ),
            EncryptableField(
                module="habits",
                field_name="description",
                display_name="Habit Descriptions", 
                description="Detailed explanations and motivations for your habits",
                recommended=True
            ),
            
            # Daily Notes module
            EncryptableField(
                module="notes",
                field_name="content",
                display_name="Daily Notes Content",
                description="Your private journal entries and daily reflections",
                recommended=True
            ),
            
            # Todos module
            EncryptableField(
                module="todos",
                field_name="title",
                display_name="Todo Titles",
                description="Task names and titles in your todo list",
                recommended=True
            ),
            EncryptableField(
                module="todos", 
                field_name="description",
                display_name="Todo Descriptions",
                description="Detailed task descriptions and notes", 
                recommended=True
            ),
            EncryptableField(
                module="todos",
                field_name="category", 
                display_name="Todo Categories",
                description="Task organization categories and labels",
                recommended=False
            ),
            
            # Reading List module
            EncryptableField(
                module="reading",
                field_name="notes",
                display_name="Reading Notes", 
                description="Your personal thoughts and notes about books",
                recommended=True
            ),
            
            # Birthdays module
            EncryptableField(
                module="birthdays",
                field_name="name",
                display_name="Contact Names",
                description="Names of people in your birthday reminders",
                recommended=False
            ),
            EncryptableField(
                module="birthdays",
                field_name="notes",
                display_name="Birthday Notes",
                description="Personal notes about relationships and memories", 
                recommended=True
            ),
            
            # Watchlist module
            EncryptableField(
                module="watchlist",
                field_name="notes", 
                display_name="Watchlist Notes",
                description="Your personal reviews and notes about movies/shows",
                recommended=True
            ),
        ]
        
        for field in default_fields:
            self.register_field(field)
    
    def register_field(self, field: EncryptableField):
        """Register a new encryptable field"""
        try:
            # Add to memory registry if not already present
            if field not in self.fields:
                self.fields.append(field)
            
            # Persist to database
            with get_db() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO encryptable_fields 
                    (module_name, field_name, field_display_name, field_description, 
                     recommended_encrypt, added_version)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (field.module, field.field_name, field.display_name, 
                      field.description, field.recommended, field.version_added))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to register field {field.module}.{field.field_name}: {e}")
    
    def get_fields_by_module(self) -> Dict[str, List[EncryptableField]]:
        """Get all fields grouped by module"""
        result = {}
        for field in self.fields:
            if field.module not in result:
                result[field.module] = []
            result[field.module].append(field)
        
        # Sort modules by common usage order
        module_order = ['habits', 'notes', 'todos', 'reading', 'birthdays', 'watchlist']
        ordered_result = {}
        
        for module in module_order:
            if module in result:
                ordered_result[module] = result[module]
        
        # Add any remaining modules
        for module, fields in result.items():
            if module not in ordered_result:
                ordered_result[module] = fields
        
        return ordered_result
    
    def get_field_key(self, module: str, field_name: str) -> str:
        """Generate standardized field key for preferences storage"""
        return f"{module}_{field_name}"
    
    def get_field_by_key(self, field_key: str) -> Optional[EncryptableField]:
        """Get field by its key"""
        try:
            module, field_name = field_key.split('_', 1)
            for field in self.fields:
                if field.module == module and field.field_name == field_name:
                    return field
        except ValueError:
            pass
        return None
    
    def get_all_fields(self) -> List[EncryptableField]:
        """Get all registered fields"""
        return self.fields.copy()
    
    def refresh_from_database(self):
        """Reload fields from database (useful after app updates)"""
        try:
            with get_db() as conn:
                rows = conn.execute("""
                    SELECT module_name, field_name, field_display_name, 
                           field_description, recommended_encrypt, added_version
                    FROM encryptable_fields 
                    ORDER BY module_name, field_name
                """).fetchall()
                
                self.fields = []
                for row in rows:
                    field = EncryptableField(
                        module=row['module_name'],
                        field_name=row['field_name'],
                        display_name=row['field_display_name'],
                        description=row['field_description'],
                        recommended=bool(row['recommended_encrypt']),
                        version_added=row['added_version'] or "1.0"
                    )
                    self.fields.append(field)
                    
        except Exception as e:
            self.logger.error(f"Failed to refresh fields from database: {e}")
    
    def get_module_display_name(self, module: str) -> str:
        """Get user-friendly module name"""
        module_names = {
            'habits': '📋 Habits',
            'notes': '📝 Daily Notes', 
            'todos': '✅ Todos',
            'reading': '📚 Reading List',
            'birthdays': '🎂 Birthdays',
            'watchlist': '🎬 Watchlist'
        }
        return module_names.get(module, f"📄 {module.title()}")


# Global field registry instance
field_registry = FieldRegistry()