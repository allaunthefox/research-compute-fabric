import express from "express";
import topologicalEngineRouter from "./connectors/topological-engine/neo4j_obsidian_connector_router.js";

const app = express();
app.use(express.json({ limit: "5mb" }));
app.use("/topology", topologicalEngineRouter);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Topological Engine listening on http://localhost:${PORT}`);
});
