from collections import defaultdict
from itertools import product
from cfg_translate import CFG

class PDA:
    def __init__(self):
        self.Q = set()          # 状态集
        self.T = set()          # 输入字母表
        self.Z = set()          # 栈字母表
        self.delta = defaultdict(list)  # 转换函数，值为(next_q, [push_symbols])的列表
        self.q0 = 'q0'         # 初始状态
        self.z0 = 'z0'         # 栈底符号
        self.var_map = {}      # 状态组合到单字母的映射

    def read_input(self):
        """读取PDA的定义"""
        print("请输入下推自动机PDA：")
        print("输入格式如下：")
        print("Q={q0,q1}")
        print("T={a,b}")
        print("Z={z0,B}")
        print("δ(q0,b,z0)={(q0,Bz0)}")
        print("δ(q0,b,B)={(q0,BB)}")
        print("δ(q0,a,B)={(q1,ε)}")
        print("δ(q1,a,B)={(q1,ε)}")
        print("δ(q1,ε,B)={(q1,ε)}")
        print("δ(q1,ε,z0)={(q1,ε)}")
        print("（以空行结束转换函数输入）")
        print("-" * 40)
        print("请开始输入：")

        # 读取状态集
        input_line = input().strip()
        pos = input_line.find("{")
        end_pos = input_line.find("}")
        self.Q.update(symbol.strip() for symbol in input_line[pos+1:end_pos].split(','))
        
        # 读取输入字母表
        input_line = input().strip()
        pos = input_line.find("{")
        end_pos = input_line.find("}")
        self.T.update(symbol.strip() for symbol in input_line[pos+1:end_pos].split(','))
        self.T.add('ε')  # 添加空串符号
        
        # 读取栈字母表
        input_line = input().strip()
        pos = input_line.find("{")
        end_pos = input_line.find("}")
        self.Z.update(symbol.strip() for symbol in input_line[pos+1:end_pos].split(','))
        
        # 读取转换函数
        while True:
            
            input_line = input().strip()
            if not input_line:
                break
            
            # 解析转换函数 δ(q0,b,z0)={(q0,Bz0)}
            left = input_line[input_line.find("(")+1:input_line.find(")")]
            q, a, z = [x.strip() for x in left.split(',')]
            
            right = input_line[input_line.find("{")+1:input_line.find("}")]
            next_q, push = [x.strip() for x in right[1:-1].split(',')]
                
                # 处理压栈符号序列
            if push != 'ε':
                push_symbols = []
                push = push.strip()
                while push:
                    for symbol in sorted(self.Z, key=len, reverse=True):
                        if push.startswith(symbol):
                            push_symbols.append(symbol)
                            push = push[len(symbol):]
                            break
                    else:
                        raise ValueError(f"无法识别的压栈符号: {push}")
                push = push_symbols
            
            self.delta[(q, a, z)].append((next_q, push if push != 'ε' else ''))

    def to_cfg(self):
        """转换为CFG"""
        cfg = CFG()
        cfg.T = self.T - {'ε'}  # 终结符不包含ε
        
        # 构造映射
        self.var_map = {}
        available_letters = [chr(i) for i in range(65, 82)]  # A-R
        next_letter_idx = 0
        
        # 先计算所需状态总数
        total_states = len(self.Q) * len(self.Q) * len(self.Z)
        use_subscript = total_states > len(available_letters)
        
        # 构造非终结符并映射到字母
        for q in sorted(self.Q):
            for gamma in sorted(self.Q):
                for z in sorted(self.Z):
                    if use_subscript:
                        # 使用下标形式 A1, A2, ...
                        self.var_map[f"[{q},{z},{gamma}]"] = f"A{next_letter_idx}"
                    else:
                        # 使用单字母
                        self.var_map[f"[{q},{z},{gamma}]"] = available_letters[next_letter_idx]
                    next_letter_idx += 1
        
        # 使用映射构建CFG
        cfg.N = set(self.var_map.values())  
        cfg.N.add('S')  # 添加起始符号
        
        # 添加起始产生式
        for q in self.Q:
            cfg.P['S'].append([self.var_map[f"[{self.q0},{self.z0},{q}]"]])
        
        # 处理转换函数
        for (q, a, z), transitions in self.delta.items():
            for next_q, push in transitions:
                if not push:  # ε情况
                    orig = f"[{q},{z},{next_q}]"
                    cfg.P[self.var_map[orig]].append([a] if a != 'ε' else ['ε'])
                else:  # 压栈情况
                    # 对每个可能的状态序列生成产生式
                    for states in product(self.Q, repeat=len(push)):
                        source = self.var_map[f"[{q},{z},{states[-1]}]"]
                        rhs = []
                        if a != 'ε':
                            rhs.append(a)
                        for i in range(len(push)):
                            if i == 0:
                                rhs.append(self.var_map[f"[{next_q},{push[0]},{states[0]}]"])
                            else:
                                rhs.append(self.var_map[f"[{states[i-1]},{push[i]},{states[i]}]"])
                        if rhs:  # 只添加非空的右侧
                            cfg.P[source].append(rhs)

        # 清理未使用的非终结符
        used_vars = {'S'}  # 起始符号必须保留
        # 收集所有产生式中使用的非终结符
        for left, rules in cfg.P.items():
            used_vars.add(left)
            for rule in rules:
                for symbol in rule:
                    if symbol in cfg.N:
                        used_vars.add(symbol)
        
        # 从N中移除未使用的非终结符
        cfg.N = used_vars

        cfg.S = 'S'
        return cfg

def main():
    """主函数"""
    pda = PDA()
    pda.read_input()
    cfg = pda.to_cfg()
    
    print("-" * 30)
    print("转换出的CFG：")
    cfg.print_grammar()
    print("-" * 30)
    print("\n简化后的CFG：")
    cfg.simplify()
    cfg.print_grammar()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
