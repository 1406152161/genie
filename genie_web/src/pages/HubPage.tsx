export default function HubPage() {
  const packs = [
    { name: "code", desc: "From requirement to complete project. 12 roles, 4 stages.", icon: "code", official: true },
    { name: "pack", desc: "Create new RolePacks. 5 roles, 3 stages.", icon: "package", official: true },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>RolePack Hub</h2>
      <p style={{ color: "#8b949e", marginBottom: 20, fontSize: 14 }}>
        RolePacks define the virtual team for each domain. Install from the hub or create your own.
      </p>

      <div className="pack-grid">
        {packs.map((p) => (
          <div className="pack-card" key={p.name}>
            <h3>{p.name}</h3>
            <p className="desc">{p.desc}</p>
            <p className="meta">
              {p.official ? "official" : "community"} | v1.0.0
            </p>
          </div>
        ))}
      </div>

      <p style={{ marginTop: 24, color: "#8b949e", fontSize: 13 }}>
        More RolePacks coming soon. Use <code>genie run pack "create a ..."</code> to create your own.
      </p>
    </div>
  );
}
