# Rferences
| **Reference** | **Key Findings & Relevance to ARCH-FL** | **Source / Citation** |
| :--- | :--- | :--- |
| **Liu et al. (2026)** | Proposes **DPSHE**, a scheme combining **Differential Privacy (DP)** and **Homomorphic Encryption** for medical imaging FL. It addresses poisoning attacks, inference attacks, and collusion, balancing model accuracy, convergence, and privacy. | *Neurocomputing* (Volume 661) |
| **Zhou et al. (2025)** | Provides a **comprehensive benchmark** of FL algorithms for medical image classification. Highlights that **no single algorithm performs best across all scenarios** and that medical datasets pose significant challenges for current FL methods. | *arXiv:2504.05238* |
| **Kitty K. Wong et al. (2024)** | Introduces **FedMLP** for **multi-label classification under task heterogeneity** (label missing). Highly relevant to use of CheXpert & MIMIC-CXR, providing a method to handle missing labels across clients. | *MICCAI 2024 Proceedings* |

These references directly support this project's focus on the challenges of **non-IID data** and **privacy-preserving techniques** in federated medical imaging.

### 📝 Purpose
*   **To justify the need for robust privacy measures:** "While FL minimizes direct data exposure, it remains vulnerable to sophisticated threats such as gradient inversion and poisoning attacks . Therefore, frameworks like ARCH-FL must integrate provable privacy guarantees, such as Differential Privacy, to ensure patient data is protected ."
*   **To highlight the challenge of data heterogeneity:** "The effectiveness of FL in real-world medical settings is hampered by non-IID data distributions across institutions. As noted in recent benchmarks, this heterogeneity significantly degrades model performance and complicates convergence . Furthermore, in multi-label settings, task heterogeneity where clients hold only partial labels is a common and under-explored challenge ."
