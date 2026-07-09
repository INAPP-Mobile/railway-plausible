import {
  defineRailway,
  github,
  group,
  postgres,
  project,
  service,
  volume,
} from "railway/iac";

export default defineRailway(() => {
  const db = postgres("plausible-postgres");
  const chData = volume("clickhouse-data", {
    region: "us-west2",
    sizeMB: 10240,
  });

  const plausible = service("plausible", {
    source: github("INAPP-Mobile/railway-plausible", { branch: "main" }),
    healthcheck: "/api/health",
    healthcheckTimeout: 300,
    env: {
      DATABASE_URL: db.env.DATABASE_URL,
      CLICKHOUSE_DATABASE_URL: "http://clickhouse:8123/plausible",
    },
  });

  const clickhouse = service("clickhouse", {
    source: github("INAPP-Mobile/railway-plausible", {
      branch: "main",
      rootDirectory: "clickhouse",
    }),
    volumeMounts: {
      "/var/lib/clickhouse": chData,
    },
  });

  const databases = group("Databases", [db, chData, clickhouse]);

  return project("plausible", {
    resources: [databases, plausible],
  });
});
