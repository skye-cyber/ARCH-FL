[![PyPI Version](https://img.shields.io/pypi/v/FLEMSIM)](https://pypi.org/project/FLEMSIM)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/skye-cyber/FLEMSIM/ci.yml?branch=main)](https://github.com/skye-cyber/FLEMSIM/actions)

---

## FLEMSIM (Federated Learning for Medical Simulation)
> Federated Medical Image Analysis Project - **Onboarding Mind Map**

## 🎯 PROJECT CORE IDENTITY
**Project Title:** ARCH-FL: Federated Learning with Differential Privacy for Medical Image Analysis
**Core Mission:** Enable collaborative AI training across hospitals without sharing raw patient data
**Key Innovation:** Privacy-preserving medical AI that respects data sovereignty

## 🔬 RESEARCH QUESTIONS
- Main: How does differential privacy impact model utility in federated medical imaging?
- Secondary: What are the effects of data heterogeneity (non-IID) on federated convergence?
- Novelty: Quantifying privacy-utility trade-off in realistic medical imaging scenarios

## 🏗️ ARCHITECTURE BLUEPRINTS

### System Components
```
Coordinator Server
├── Model Aggregation (FedAvg)
├── Client Management
├── Privacy Accounting
└── Evaluation Dashboard

Client Nodes (Simulated)
├── Local Training Loop
├── Differential Privacy Module
├── Secure Communication
└── Data Loader (Non-IID)
```

### Technical Stack
- **Deep Learning:** PyTorch + PyTorch Lightning
- **Privacy:** Opacus/TensorFlow Privacy
- **Data Processing:** Dask + Pandas 
- **Medical Data:** MedMNIST + COVIDx CXR
- **Visualization:** Streamlit/Plotly/Matplotlib
- **Experiment Tracking:** MLflow/Weights & Biases

## 📊 DATA STRATEGY

### Datasets to Use
1. **Primary:** MedMNIST (PneumoniaMNIST)
2. **Validation:** COVIDx CXR (chest X-rays)
3. **Synthetic:** Generated non-IID splits

### Data Partitioning Schemes
- IID (baseline)
- Label-skew non-IID
- Quantity-skew non-IID
- Realistic hospital distribution

## ⚙️ EXPERIMENT DESIGN

### Variables to Test
- **Privacy Levels:** ε = [1, 2, 4, 8, ∞] (no DP)
- **Client Fractions:** [0.1, 0.3, 0.5]
- **Non-IID Severity:** [low, medium, high]
- **Model Architectures:** [SimpleCNN, ResNet-18]

### Evaluation Metrics
- **Primary:** Test Accuracy vs Privacy Budget
- **Secondary:** Convergence Speed, Communication Efficiency
- **Privacy:** Formal (ε,δ)-DP guarantees
- **Fairness:** Performance variance across clients

## 🚀 EXECUTION ROADMAP

### Phase 1: Foundation (Weeks 1-3)
- [ ] Set up federated learning baseline (no DP)
- [ ] Implement FedAvg coordinator
- [ ] Create non-IID data partitioning
- [ ] Establish evaluation pipeline

### Phase 2: Privacy Integration (Weeks 4-6)  
- [ ] Integrate differential privacy (DP-SGD)
- [ ] Implement privacy accounting
- [ ] Run privacy-utility trade-off experiments
- [ ] Optimize DP parameters

### Phase 3: Advanced Analysis (Weeks 7-9)
- [ ] Test under extreme non-IID conditions
- [ ] Compare with centralized baseline
- [ ] Analyze communication efficiency
- [ ] Conduct ablation studies

### Phase 4: Polish & Documentation (Weeks 10-12)
- [ ] Build visualization dashboard
- [ ] Write academic paper
- [ ] Prepare demo video
- [ ] Document code and findings

## 🎓 ACADEMIC POSITIONING

### Key Differentiators
- **Practical Focus:** Realistic medical imaging constraints
- **Rigorous Evaluation:** Comprehensive privacy-utility analysis  
- **Reproducible:** Clean code with ablation studies
- **Accessible:** Works on consumer hardware

### Expected Contributions
1. Concrete guidelines for DP in medical federated learning
2. Analysis of non-IID effects on private federated learning
3. Open-source implementation for community use
4. Baseline results for future research

## 🔍 CRITICAL SUCCESS FACTORS

### Technical Must-Haves
- [ ] Formal privacy guarantees with DP proof
- [ ] Significant non-IID performance analysis  
- [ ] Comparison to centralized upper bound
- [ ] Reproducible experimental setup

### Academic Must-Haves
- [ ] Clear hypothesis testing
- [ ] Statistical significance testing
- [ ] Comparison to relevant baselines
- [ ] Limitations and future work discussion

## ⚠️ RISK MITIGATION

### Technical Risks
- **DP noise destroys utility:** Start with weak privacy, gradually strengthen
- **Non-IID prevents convergence:** Implement FedProx as backup algorithm
- **Medical data complexity:** Start with MedMNIST, scale to CXR if time permits

### Timeline Risks  
- **Scope creep:** Stick to core research questions
- **Implementation delays:** Use pre-built components where possible
- **Experimental runs too long:** Use cloud credits for parallel experiments

## 📝 QUICKSTART COMMANDS
```bash
# Environment setup
conda create -n fl-medical python=3.9 
or
pip venv fl-medical

pip install torch torchvision opacus streamlit

# Run baseline experiment
python main.py --mode iid_baseline --dp_epsilon inf

# Run DP experiment  
python main.py --mode non_iid --dp_epsilon 2.0

# Launch dashboard
streamlit run dashboard.py
```

## Project Structure
```text
FLEMSIM/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── config/
│   ├── base.yaml
│   ├── experiment/
│   │   ├── iid_baseline.yaml
│   │   ├── non_iid_dp.yaml
│   │   └── ablation.yaml
│   └── model/
│       ├── simple_cnn.yaml
│       └── resnet18.yaml
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── coordinator.py      # FedAvg server implementation
│   │   ├── client.py
│   │   └── aggregation.py
│   ├── privacy/
│   │   ├── dp_engine.py        # DP-SGD integration 
│   │   ├── accounting.py
│   │   └── noise_mechanisms.py
│   ├── data/
│   │   ├── loaders.py
│   │   ├── partitioning.py     # Non-IID data splits
│   │   └── datasets.py
│   ├── models/
│   │   ├── architectures.py
│   │   └── utils.py
│   ├── training/
│   │   ├── local_trainer.py
│   │   └── fedavg.py
│   └── utils/
│       ├── logger.py
│       ├── metrics.py
│       └── visualization.py
├── experiments/
│   ├── run_baseline.py
│   ├── run_dp_experiment.py    # Main experiment runner
│   ├── run_non_iid.py
│   └── ablation/
│       ├── client_sampling.py
│       └── dp_params.py
├── tests/
│   ├── test_coordinator.py
│   ├── test_dp_engine.py
│   ├── test_data_partitioning.py
│   └── conftest.py
├── docs/
│   ├── api/
│   ├── setup_guide.md
│   └── experiment_protocols.md
├── results/
│   ├── figures/
│   ├── logs/
│   └── checkpoints/
└── dashboard/
    ├── app.py                   # Streamlit visualization
    ├── components/
    └── assets/
```

## 🆘 Support

For support and questions:
- Check the documentation
- Open an issue on GitHub
- Contact the development team

## Contributing
Fore more information on how to contribute to this project see [contribbuting](CONTRIBUTING.md)

## **Contributors**
- **[Wambua]** – Repo Admin


## Acknowledgements

[Shields.io](https://shields.io/) – Status badges 


---
## 💡 Author
``Skye - Wambua``
- Made with 💻 and ☕ in Kenya

---

GitHub’s README guidelines 
