from sympy import symbols, Eq, solve
p = symbols('p')
post_aggregate_accuracy = 0.957714286
consistent_rate = 0.69
print(f'一致率{round(consistent_rate*100,2)}%')
equation = Eq(post_aggregate_accuracy * p * p + (1 - post_aggregate_accuracy) * (1 - p) * p + post_aggregate_accuracy * (1 - p) * (1 - p) + (1 - post_aggregate_accuracy) * p * (1 - p), consistent_rate)
p_value = solve(equation, p)
print(f'聚合前准确率{round(max(p_value)*100,2)}%')
from math import comb
p = max(p_value)
q = 1 - p
n = 5
probability = sum(comb(n, i) * (p ** i) * (q ** (n - i)) for i in range((n+1)//2, n + 1))
print(f'聚合后准确率{round(probability*100,2)}%')
