
db.sites.update(
   { "site.tower_type": "lattice" },
   { $set: { "site.tower_type": "Lattice" } }, 
   {multi: true }
)
