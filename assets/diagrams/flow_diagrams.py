from dotflow import create_flow

flow = create_flow('Conceptual_Framework', theme="blue")
(
    flow
    # Create nodes
    .process(node_id='dataset', label="Medical Image Datasets\n (CheXpert, MIMIC)")
    .process("ARCHFL", "ARCH-FL Federated Learning Pipeline")
    .process("Evaluation", "Evaluation & Output")
    .process("technical_components", """Core Technical Components\n1. Non-IID Data Partitioning \n(Dirichlet Distribution)\n2. Local Model Training\n(Multi-label CNN)\n3. Privacy Mechanism \n(Sensitivity-Aware DP)\n4. Federated Aggregation (FedAvg)""")
    .process('feedback_loop', 'Feedback & Analysis Loop\n- Privacy-Utility Trade-off Analysis \n- Impact of Non-IID Severity \n- Multi-label Performance (AUROC)')
    # Connect nodes
    .connect('dataset', 'ARCHFL', 'Data In', arrowhead="arrow")
    .connect('ARCHFL', 'Evaluation', 'Data Out', arrowhead="arrow")
    .connect('ARCHFL', 'technical_components', 'System Components', arrowhead="arrow")
    .connect('technical_components', 'feedback_loop', arrowhead="arrow")
    # Render to png
    .render('dot', 'Conceptual_Framework.dot')
)
