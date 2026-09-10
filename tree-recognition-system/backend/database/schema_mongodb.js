// MongoDB Schema and Configuration for Tree Recognition System
// Run this script using: mongosh <your-database-name> < schema_mongodb.js

// ===== COLLECTIONS =====

// Trees Collection
db.createCollection("trees", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["tree_id", "registered_date"],
      properties: {
        tree_id: {
          bsonType: "string",
          description: "Unique identifier for the tree"
        },
        tree_type: {
          bsonType: "string",
          description: "Type or species of the tree"
        },
        tree_species: {
          bsonType: "string",
          description: "Scientific name of the tree species"
        },
        location_lat: {
          bsonType: "double",
          description: "Latitude coordinate"
        },
        location_lng: {
          bsonType: "double",
          description: "Longitude coordinate"
        },
        location_address: {
          bsonType: "string",
          description: "Human-readable address"
        },
        metadata: {
          bsonType: "object",
          description: "Additional metadata about the tree"
        },
        registered_date: {
          bsonType: "date",
          description: "Date when tree was first registered"
        },
        last_updated: {
          bsonType: "date",
          description: "Date when tree data was last updated"
        },
        status: {
          bsonType: "string",
          enum: ["active", "inactive", "removed"],
          description: "Current status of the tree"
        }
      }
    }
  }
});

// Tree Features Collection
db.createCollection("tree_features", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["tree_id", "features", "extraction_date"],
      properties: {
        tree_id: {
          bsonType: "string",
          description: "Reference to tree"
        },
        features: {
          bsonType: "array",
          description: "Feature vector array"
        },
        image_path: {
          bsonType: "string",
          description: "Path to the image used for feature extraction"
        },
        extraction_date: {
          bsonType: "date",
          description: "Date when features were extracted"
        }
      }
    }
  }
});

// Tree Images Collection
db.createCollection("tree_images", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["tree_id", "image_path", "uploaded_date"],
      properties: {
        tree_id: {
          bsonType: "string",
          description: "Reference to tree"
        },
        image_path: {
          bsonType: "string",
          description: "Path to stored image"
        },
        image_type: {
          bsonType: "string",
          enum: ["registration", "observation", "analysis"],
          description: "Type of image"
        },
        uploaded_date: {
          bsonType: "date",
          description: "Date when image was uploaded"
        }
      }
    }
  }
});

// Tree Observations Collection
db.createCollection("tree_observations", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["tree_id", "observation_date"],
      properties: {
        tree_id: {
          bsonType: "string",
          description: "Reference to tree"
        },
        features: {
          bsonType: "array",
          description: "Feature vector for this observation"
        },
        image_path: {
          bsonType: "string",
          description: "Path to observation image"
        },
        health_status: {
          bsonType: "string",
          description: "Health status of the tree"
        },
        growth_stage: {
          bsonType: "string",
          description: "Growth stage of the tree"
        },
        notes: {
          bsonType: "string",
          description: "Additional notes"
        },
        observation_date: {
          bsonType: "date",
          description: "Date of observation"
        }
      }
    }
  }
});

// ===== INDEXES =====

// Trees Collection Indexes
db.trees.createIndex({ "tree_id": 1 }, { unique: true });
db.trees.createIndex({ "tree_type": 1 });
db.trees.createIndex({ "tree_species": 1 });
db.trees.createIndex({ "status": 1 });
db.trees.createIndex({ "registered_date": -1 });
db.trees.createIndex({ "location_lat": 1, "location_lng": 1 });

// Geospatial index for location-based queries
db.trees.createIndex({ 
  location: "2dsphere" 
});

// Tree Features Indexes
db.tree_features.createIndex({ "tree_id": 1 });
db.tree_features.createIndex({ "extraction_date": -1 });
db.tree_features.createIndex({ "tree_id": 1, "extraction_date": -1 });

// Tree Images Indexes
db.tree_images.createIndex({ "tree_id": 1 });
db.tree_images.createIndex({ "uploaded_date": -1 });
db.tree_images.createIndex({ "image_type": 1 });

// Tree Observations Indexes
db.tree_observations.createIndex({ "tree_id": 1 });
db.tree_observations.createIndex({ "observation_date": -1 });
db.tree_observations.createIndex({ "tree_id": 1, "observation_date": -1 });
db.tree_observations.createIndex({ "health_status": 1 });

// ===== SAMPLE DATA (for testing) =====
/*
db.trees.insertMany([
  {
    tree_id: "tree-001",
    tree_type: "Terak",
    tree_species: "Populus tremula",
    location_lat: 41.311151,
    location_lng: 69.279737,
    location_address: "Toshkent, O'zbekiston",
    metadata: {
      age: 10,
      height: 15.5,
      diameter: 0.5
    },
    registered_date: new Date(),
    last_updated: new Date(),
    status: "active"
  },
  {
    tree_id: "tree-002",
    tree_type: "Qarag'ay",
    tree_species: "Pinus sylvestris",
    location_lat: 41.326418,
    location_lng: 69.228443,
    location_address: "Toshkent, O'zbekiston",
    metadata: {
      age: 15,
      height: 20.0,
      diameter: 0.7
    },
    registered_date: new Date(),
    last_updated: new Date(),
    status: "active"
  }
]);
*/

print("MongoDB schema va indexes muvaffaqiyatli yaratildi!");
print("Collections: trees, tree_features, tree_images, tree_observations");


