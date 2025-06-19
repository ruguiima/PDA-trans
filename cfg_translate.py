from collections import defaultdict

class CFG:
    """上下文无关文法类"""
    def __init__(self):
        self.P = defaultdict(list)  # 产生式集合
        self.N = set()              # 非终结符集合
        self.T = set()              # 终结符集合
        self.S = ''                 # 起始符号

    def read_input(self):
        """从标准输入读取文法规则"""
        print("请输入上下文无关文法：")
        print("输入格式如下：")
        print("N={S,A,B}")
        print("T={a,b,c}")
        print("P:")
        print("  S->ASB|ε")
        print("  A->aAS|a")
        print("  B->SBS|A|bb")
        print("S=S")
        print("-" * 40)
        print("请开始输入：")

        # 读取并解析非终结符集合
        input_line = input()
        pos = input_line.find("N={")
        end_pos = input_line.find("}")
        self.N.update(symbol.strip() for symbol in input_line[pos+3:end_pos].split(','))
        
        # 读取并解析终结符集合
        input_line = input()
        pos = input_line.find("T={")
        end_pos = input_line.find("}")
        self.T.update(symbol.strip() for symbol in input_line[pos+3:end_pos].split(','))
        
        input()
        # 解析产生式集合
        while True:
            input_line = input()
            if input_line[0] == 'S':
                break
                
            arrow_pos = input_line.find("->")
            key = input_line[1:arrow_pos].strip()
            value = []
            productions = input_line[arrow_pos + 2:].split('|')
            
            for prod in productions:
                rhs = []
                remaining = prod.strip()
                while remaining:
                    for symbol in sorted(self.N | self.T | {'ε'}, key=len, reverse=True):
                        if remaining.startswith(symbol):
                            rhs.append(symbol)
                            remaining = remaining[len(symbol):]
                            break
                    
                    else:
                        raise ValueError(f"无法识别的符号: {remaining}")
                            
                if rhs:  # 确保不添加空的产生式
                    value.append(rhs)
                            
            self.P[key] = value
        
        # 读取起始符号
        self.S = input_line[input_line.find("=")+1:].strip()

    def print_grammar(self):
        """输出文法规则"""
        print("N={" + ",".join(sorted(self.N)) + "}")
        print("T={" + ",".join(sorted(self.T)) + "}")
        
        print("P:")
        for key in sorted(self.P.keys()):
            print(f"\t{key}->", end="")
            print('|'.join(sorted(''.join(rhs) for rhs in self.P[key])))
        
        print(f"S={self.S}")

    def eliminate_epsilon(self):
        """消除ε产生式"""
        # 找到可以直接推出ε的非终结符
        eps_generating = set()
        for key, value in self.P.items():
            if any(len(rhs) == 1 and rhs[0] == 'ε' for rhs in value):
                eps_generating.add(key)
        
        # 不断扩展eps_generating集合
        while True:
            old_size = len(eps_generating)
            for key, value in self.P.items():
                if key not in eps_generating:
                    for rhs in value:
                        if all(sym in eps_generating for sym in rhs):
                            eps_generating.add(key)
                            break
            if len(eps_generating) == old_size:
                break
        
        # 生成新的产生式集合
        new_P = defaultdict(list)
        for key, value in self.P.items():
            new_rhs_list = []
            for rhs in value:
                total_eps = sum(1 for sym in rhs if sym in eps_generating)
                
                for num in range(1 << total_eps):
                    new_rhs = []
                    eps_count = 0
                    for sym in rhs:
                        if sym in eps_generating:
                            if (num >> eps_count) & 1:
                                new_rhs.append(sym)
                            eps_count += 1
                        else:
                            new_rhs.append(sym)
                            
                    if new_rhs and new_rhs[0] != 'ε':
                        new_rhs_list.append(new_rhs)
                                        
            if new_rhs_list:
                new_P[key] = list(map(list, dict.fromkeys(map(tuple, new_rhs_list))))

        
        # 处理起始符号
        if self.S in eps_generating:
            new_S = 'S1'
            new_P[new_S] = [[self.S], ['ε']]
            self.S = new_S
            self.N.add(self.S)
        
        self.P = new_P

    def eliminate_single(self):
        """消去单产生式"""
        new_productions = defaultdict(list)
        
        for A in self.N:
            new_nonterminals = {A}
            new_productions[A] = []
            
            # 找出所有可以直接推出的非终结符并扩展
            while True:
                prev_size = len(new_nonterminals)
                for B in list(new_nonterminals):
                    if B in self.P:
                        for rhs in self.P[B]:
                            if len(rhs) == 1 and rhs[0] in self.N:
                                new_nonterminals.add(rhs[0])
                if len(new_nonterminals) == prev_size:
                    break
            
            # 构建新的产生式
            for B in new_nonterminals:
                if B in self.P:
                    new_productions[A].extend(
                        rhs for rhs in self.P[B]
                        if len(rhs) != 1 or rhs[0] in self.T or rhs[0] == 'ε'
                    )
            
            # 去重和处理空产生式
            if new_productions[A]:
                new_productions[A].sort()
                new_productions[A] = list(map(list, dict.fromkeys(map(tuple, new_productions[A]))))
            else:
                del new_productions[A]
        
        self.P = new_productions

    def eliminate_useless(self):
        """消去无用符号"""
        # 找出所有可能产生终结符串的非终结符
        N1 = {key for key, value in self.P.items()
              if any(all(sym in self.T or sym == 'ε' for sym in rhs)
                    for rhs in value)}
        
        # 扩展N1直到不再变化
        while True:
            N0 = N1.copy()
            for key, value in self.P.items():
                if any(all(sym in N0 or sym in self.T or sym == 'ε' for sym in rhs)
                      for rhs in value):
                    N1.add(key)
            if N0 == N1:
                break
        
        self.N = N1
        
        # 删除不在N1中的产生式
        self.P = {k: [rhs for rhs in v if all(sym in N1 or sym in self.T or sym == 'ε' for sym in rhs)]
                 for k, v in self.P.items() if k in N1}
        
        # 找出从起始符号可达的符号
        reachable = {self.S}
        while True:
            old_size = len(reachable)
            new_symbols = {sym for key in reachable if key in self.P
                         for rhs in self.P[key]
                         for sym in rhs}
            reachable.update(new_symbols)
            if len(reachable) == old_size:
                break
        
        # 更新集合
        self.N = {sym for sym in self.N if sym in reachable}
        self.T = {sym for sym in self.T if sym in reachable}
        self.P = {k: v for k, v in self.P.items() if k in reachable}

    def simplify(self):
        """简化文法"""
        self.eliminate_epsilon()
        self.eliminate_single()
        self.eliminate_useless()

def main():
    """主函数"""
    cfg = CFG()
    cfg.read_input()
    cfg.simplify()
    print("-" * 30)
    print("简化后的文法：")
    cfg.print_grammar()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
