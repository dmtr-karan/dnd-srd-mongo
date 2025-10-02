// File: scripts/feature_validator.mongo.js
// Usage:
//   mongosh "mongodb://localhost:27017/dnd_srd" scripts/feature_validator.mongo.js

// Create collection if missing with validator; otherwise tighten via collMod.
const dbname = db.getName();
print(`Applying $jsonSchema validator on 'features' in db=${dbname}`);

const schema = {
  bsonType: "object",
  required: ["class_name","class_srd_id","edition","level","name","slug","description_md","source","license","meta"],
  additionalProperties: false,
  properties: {
    _id:            { bsonType: "objectId" },
    class_name:     { bsonType: "string", minLength: 1 },
    class_srd_id:   { bsonType: "string", pattern: "^class:[a-z0-9-]+:srd-5-1$" },
    edition:        { bsonType: "string", enum: ["5e-2014"] },
    level:          { bsonType: "int", minimum: 1, maximum: 20 },
    name:           { bsonType: "string", minLength: 1 },
    slug:           { bsonType: "string", pattern: "^[a-z0-9-]+-l([1-9][0-9]*)$" },
    srd_feature_id: { bsonType: ["string","null"] },
    description_md: { bsonType: "string", minLength: 1 },
    source:         { bsonType: "string", minLength: 1 },
    license:        { bsonType: "string", enum: ["CC-BY-4.0"] },
    meta: {
      bsonType: "object",
      required: ["imported_at","import_version"],
      additionalProperties: false,
      properties: {
        imported_at:    { bsonType: "string", minLength: 1 },
        import_version: { bsonType: "int", minimum: 1 }
      }
    }
  }
};

const hasFeatures = db.getCollectionNames().includes("features");
if (!hasFeatures) {
  db.createCollection("features", {
    validator: { $jsonSchema: schema },
    validationLevel: "strict",
    validationAction: "error",
  });
  print("Created 'features' with validator.");
} else {
  const res = db.runCommand({
    collMod: "features",
    validator: { $jsonSchema: schema },
    validationLevel: "strict",
    validationAction: "error",
  });
  printjson(res);
}
