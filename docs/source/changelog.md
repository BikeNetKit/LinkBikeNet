# Changelog

## Version 0.8.3 (2026-10-05)

- 🐛 Added missing lcc_steps
- 🐛 Accounted for all unintended connected components
- ♻️ Refactored component linking

## Version 0.8.2 (2026-10-01)

- 📄 Added missing license file
- 🐛 Removed motor_vehicle condition from pbi mapping

## Version 0.8.1 (2026-09-30)

- 🐛 Fixed L2C crashing before 100%
- 💄 Polished tqdm table

## Version 0.8.0 (2026-09-29)

- 🐛 Fixed shortest path overlaps with bike infrastructure
- 🐛 Changed euclidian to network distances for components
- 🐛 Fixed components connected underway not considered in L2S strategy
- ✨ Implemented heuristic of top N closest component/node candidates
- ✨ Extended bike network definition
- ✨ Added link_length and num_comps_added fields
- 💄 Finished styling and polishing tqdm progress bars

## Version 0.7.2 (2026-09-25)

- ✨ added boundary file import
- ✨ added tqdm progress bars

## Version 0.7.1 (2026-09-07)

- 🐛 remove import path from function definition

## Version 0.7.0 (2026-09-07)

- 🐛 implemented automatic crs matching to ensure correct edge lengths

## Version 0.6.0 (2026-08-19)

- ✨ implemented closest-to-closest algorithm
- ✨ added import option for street network
- ✨ added network connectivity metrics to output and changed file naming
- 🔧 added settings.py

## Version 0.5.0 (2026-07-27)

- ✨Initial release ✨
- 🔧Full reimplementation of code from paper "Data-driven strategies for optimal bicycle network growth" https://github.com/nateraluis/bicycle-network-growth
- ⬆️Automated testing via pytest as well as pipeline for package deployment to pip
