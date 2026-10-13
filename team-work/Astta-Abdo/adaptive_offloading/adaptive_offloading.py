from offloading_rl.config import FeatureConfig
from offloading_rl.state import StateSpace


latency = FeatureConfig(
    name="latency",
    unit="ms",
    thresholds=(50, 150),
    labels=("Low", "Medium", "High"),
    min_value=0,
    max_value=300,
)

space = StateSpace((latency,))

print("Number of states:", space.n_states)
print("Low latency:", space.to_state_id({"latency": 25}))
print("Medium latency:", space.to_state_id({"latency": 100}))
print("High latency:", space.to_state_id({"latency": 200}))
