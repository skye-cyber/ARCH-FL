---
dataset_info:
  features:
  - name: Path
    dtype: string
  - name: Sex
    dtype:
      class_label:
        names:
          '0': Male
          '1': Female
  - name: Age
    dtype: int64
  - name: Frontal/Lateral
    dtype:
      class_label:
        names:
          '0': Frontal
          '1': Lateral
  - name: AP/PA
    dtype:
      class_label:
        names:
          '0': AP
          '1': PA
          '2': ''
  - name: No Finding
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Enlarged Cardiomediastinum
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Cardiomegaly
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Lung Opacity
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Lung Lesion
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Edema
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Consolidation
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Pneumonia
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Atelectasis
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Pneumothorax
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Pleural Effusion
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Pleural Other
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Fracture
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: Support Devices
    dtype:
      class_label:
        names:
          '0': unlabeled
          '1': uncertain
          '2': absent
          '3': present
  - name: image
    dtype: image
  splits:
  - name: train
    num_bytes: 11163990852.674
    num_examples: 223414
  - name: validation
    num_bytes: 12063657
    num_examples: 234
  download_size: 11466560036
  dataset_size: 11176054509.674
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: validation
    path: data/validation-*
task_categories:
- image-classification
pretty_name: chexpert
size_categories:
- 100K<n<1M
---

# CheXpert

CheXpert is a large dataset of chest X-rays and competition for automated chest x-ray interpretation, which features uncertainty labels and radiologist-labeled reference standard evaluation sets.

[https://stanfordmlgroup.github.io/competitions/chexpert/](https://stanfordmlgroup.github.io/competitions/chexpert/)

# Warning on AP/PA label

I could not find in the paper a mapping from the 0/1 label to AP/PA, so I assumed 0=AP and 1=PA. Looking at a few images this seems to be correct, but I'm not a radiologist.

```
@inproceedings{irvin2019chexpert,
  title={Chexpert: A large chest radiograph dataset with uncertainty labels and expert comparison},
  author={Irvin, Jeremy and Rajpurkar, Pranav and Ko, Michael and Yu, Yifan and Ciurea-Ilcus, Silviana and Chute, Chris and Marklund, Henrik and Haghgoo, Behzad and Ball, Robyn and Shpanskaya, Katie and others},
  booktitle={Proceedings of the AAAI conference on artificial intelligence},
  volume={33},
  number={01},
  pages={590--597},
  year={2019}
}
```
