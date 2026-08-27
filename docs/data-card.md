# Data card

## Training dataset

- **Repository:** `nikolkoo/SatelliteSegmentation`
- **Pinned revision:** `6109f61547ea2a3cdb5130983837790628a23821`
- **License reported upstream:** CC BY 4.0
- **Samples:** 790 paired RGB image/mask tiles
- **Shape:** 256 × 256 pixels
- **Stated ground sampling distance:** 10 m/pixel
- **Imagery:** Sentinel-2 RGB
- **Labels:** ESA WorldCover-derived categorical masks
- **Geographic focus:** Norway

The upstream dataset provides one source split. RasterScope generates a deterministic split with seed 42: 553 train, 118 validation, and 119 test samples.

## Operational taxonomy

RasterScope remaps source labels into seven classes. Source value 0 is ignored.

| Model class | Source values | Training pixels | Share of labeled training pixels |
| --- | --- | ---: | ---: |
| Tree cover | 10 | 25,519,970 | 70.4% |
| Low vegetation | 20, 30, 100 | 3,286,480 | 9.1% |
| Cropland | 40 | 2,644,539 | 7.3% |
| Built-up | 50 | 1,491,113 | 4.1% |
| Exposed terrain | 60, 70 | 58,661 | 0.16% |
| Permanent water | 80 | 3,209,576 | 8.9% |
| Herbaceous wetland | 90 | 24,925 | 0.07% |

The imbalance is severe. Weighted cross-entropy and Dice loss reduce but do not remove it; the two rarest classes are not learned in the published run.

## Temporal demonstration scenes

The source dataset is not temporally paired. RasterScope therefore acquires two aligned Sentinel-2 L2A scene pairs from the Microsoft Planetary Computer STAC catalog for product demonstration.

### Innlandet, Norway

- Before: `S2B_MSIL2A_20200614T104629_R051_T32VNN_20200827T094730`
- After: `S2B_MSIL2A_20240812T104629_R051_T32VNN_20240812T134520`
- Role: comparison near the training geography

### São José dos Campos, Brazil

- Before: `S2A_MSIL2A_20200913T131251_R138_T23KLQ_20200918T161423`
- After: `S2A_MSIL2A_20240505T131241_R138_T23KLQ_20240505T191132`
- Role: deliberate domain-shift demonstration

These scenes have no local ground-truth masks. Their changes are model predictions and must not be interpreted as measured environmental outcomes.

## Intended use

- education and portfolio demonstration;
- prototyping local semantic-segmentation interfaces;
- illustrating auditable change-summary pipelines;
- qualitative inspection of model behavior.

## Out-of-scope use

- cadastral or legal boundary decisions;
- ecological impact assessment;
- emergency response;
- enforcement or surveillance decisions;
- claims of causal land-use change;
- accuracy claims outside the fixed held-out dataset.

## Known risks

- Geographic and seasonal bias toward Norway.
- RGB input omits red-edge, NIR, SWIR, and temporal features.
- Label noise can arise from resolution and acquisition-date differences between imagery and WorldCover.
- Rare-class underrepresentation makes macro metrics volatile.
- Resizing arbitrary uploads can distort small objects and assumes images are spatially aligned.

## Provenance and updates

Dataset revision, sample counts, seed, and split indices are persisted in `config.yaml`, `artifacts/runs/dataset_audit.json`, and `data/processed/splits.json`. A data update should create a new split and evaluation record rather than silently overwriting these artifacts.
