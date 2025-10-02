/**
 * SRD prototype — canonical indexes
 *
 * Usage:
 *   # Local default DB
 *   mongosh "mongodb://localhost:27017/dnd_srd" scripts/indexes.mongo.js
 *
 * Notes:
 * - Safe to run repeatedly (idempotent). Existing compatible indexes are retained;
 *   MongoDB will no-op identical createIndex calls.
 * - Collections: classes (embedded features_by_level), features (normalized).
 */

// classes
db.classes.createIndex({ srd_id: 1 }, { unique: true });
db.classes.createIndex({ name: 1 });

// features (normalized)
db.features.createIndex({ class_srd_id: 1, level: 1, slug: 1 }, { unique: true });
db.features.createIndex({ class_name: 1, level: 1 });
