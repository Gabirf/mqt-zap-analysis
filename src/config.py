from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ZAP_OUTPUT = WORKSPACE_ROOT / "output" / "ZAP"
QMAP_OUTPUT = WORKSPACE_ROOT / "output" / "QMAP"
CIRCUIT_INPUT = WORKSPACE_ROOT / "input" / "circuits"
ARCH_INPUT = WORKSPACE_ROOT / "input" / "arch"

FIDEL_Q1 = 0.9997
FIDEL_Q2 = 0.995
FIDEL_CROSS = 0.9975
FIDEL_TRAN = 0.999
FIDEL_TALK = 0.9975
ACC = 2.75

t_1 = 1.0
t_2 = 0.2
t_t = 15.0