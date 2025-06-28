from collections import Counter

stats = Counter()
with open('lookup_method_stats.log', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) == 4:
            _, _, method, success = parts
            stats[(method, success)] += 1

print('Method\tSuccess\tCount')
for (method, success), count in stats.most_common():
    print(f'{method}\t{success}\t{count}') 