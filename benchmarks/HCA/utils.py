__author__ = "Ibrahim Abu Kharmeh"
__copyright__ = "Copyright 2021, Huawei R&D Bristol"
__license__ = "BSD 2-Clause"
__version__ = "0.4.0"




from collections import Counter
import re


def flat_list(list_of_lists, mode=0):
    if (mode == 0):
        return [item for sublist in list_of_lists for item in sublist]
    elif (mode ==1):
        flatlist = list()
        for lista in list_of_lists:
            flatlist.append(lista[0]+":"+str(len(lista)))
        return flatlist
    else:
        flatlist = list()
        for lista in list_of_lists:
            flatlist.append(" ".join(lista))
        return flatlist

def count_insts(inst_list,mode=0):
    flatlist = flat_list(inst_list,mode)
    return Counter(flatlist)

def count_insts_num_before_overwritten(inst_list):
    length_dict = {}
    for li in inst_list:
        if len(li) not in length_dict:
            length_dict[len(li)] = 1
        else:
            length_dict[len(li)] += 1   
    return length_dict 

def count_first_insts(inst_list):
    new_list = []
    for li in inst_list:        
        li = [li[0]]
        new_list.append(li)  
    return count_insts(new_list) 

def count_single_use_insts(inst_list):
    new_list = []
    for li in inst_list:
        if len(li) == 1:        
            li = [li[0]]
            new_list.append(li)  
    return count_insts(new_list) 

def filter_instruction_chains (mnemonics,instructions,woe_insensitive=True,min_chain=0,additional_condition = lambda unused: True):
    # TODO maybe introduce chainwise additional conditions !
    ''' Filter Instruction dependancy chains for a given dependant instruction
    if woe_insensitive is True, then will match regardless of WoE'''
    opt_inst = list()
    for chain in mnemonics:
        for ins in chain:
            if ((((ins["Instruction"] in  instructions) or 
                (woe_insensitive and ("c." in ins["Instruction"]) and  ins["Instruction"][2:] in instructions))
                and len(chain) >= min_chain and additional_condition(ins))):
                opt_inst.append(chain)
                break
    return opt_inst       

# Instructions Categories 
categories = [('jump_imm', re.compile('beqi|blti|bnei|bgei|bltui|bgeui')),
                ('branch', re.compile('beq|bg|bl|bn')),
                ('load_imm', re.compile('li|lui|auipc')),
                ('custom', re.compile(
                    'uxt|addshf|subshf|orshf|xorshf|andshf|sb|lbu|sh|lhu|muliadd|wfi|sgtz')),
                ('multiple', re.compile('pop|popret|push')),
                ('system', re.compile('csr|fence')),
                ('alu_imm', re.compile('addi|subi|muli|andi|ori|slli|noti|srli|xori|srai')), 
                ('alu', re.compile(
                    'add|sub|mul|and|or|sll|not|srl|rem|mv|div|seq|slt|xor|sne|neg|ecall|ebreak|sra|flw|fmad|fnma')),
                ('load', re.compile('lw|lh|lb|ld')),
                ('store', re.compile('sw|sd')),
                ('jump', re.compile('ret|j16|jal|jr|jalr|j$')),
                # FIXME F,A,B extensions were added to categories to allow isntfreq work with them
                # but they need to be parsed and their various fields need to be populated !  
                ('f_ext', re.compile("fabs|fadd|fclass|fcvt|fdiv|feq|fld|fle|flt|fmax|fmin|fmsub|fmul|fmv")),
                ("a_ext",re.compile("amoadd|amomaxu|amoor|amoswap")),
                ('b_ext', re.compile('pack|minu|maxu|max|ctz|grevi|min|rori|rol|xnor|pcnt')),
                ]


# Jump Sub Categories FIXME inconsistent naming ! 
jump_categories = [('cond_branch', re.compile('beq|bg|bl|bn|beqi|blti|bnei|bgei|bltui|bgeui')),
                    ('jumps', re.compile('jal|ret|jr|j16|j$'))]

# Generic ra patterns ! 
hexadecimal_ptn = re.compile('[a-f0-9]+$')



# Unroll Name !!
ABI_Reg_Names = ["zero","ra","sp","gp","tp","t0","t1","t2","t3","t4","t5","t6","s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11","a0","a1","a2","a3","a4","a5","a6","a7"]
Reg_Names = {"zero":"x0","ra":"x1","sp":"x2","gp":"x3","tp":"x4","t0":"x5","t1":"x6","t2":"x7","s0":"x8","s1":"x9","a0":"x10","a1":"x11","a2":"x12","a3":"x13","a4":"x14","a5":"x15","a6":"x16","a7":"x17","s2":"x18","s3":"x19","s4":"x20","s5":"x21","s6":"x22","s7":"x23","s8":"x24","s9":"x25","s10":"x26","s11":"x27","t3":"x28","t4":"x29","t5":"x30","t6":"x31"}


def Categories_Reg(reg):
    Special = ["zero","ra","sp","gp","tp"]
    if (reg in Special):
        return "Special"
    else:
        return reg[0]

reg_within = lambda reg:  int(Reg_Names[reg][1:]) > 7 and int(Reg_Names[reg][1:]) < 16


def inst_abi_to_non(inst):
    '''Converts a dictionary entry (Instruction) to standard register naming '''
    regs = []
    for register in inst['Destination']:
        regs.append(Reg_Names[register])
    inst['Destination'] = set(regs)

    for register in inst["Source"]:
        regs.append(Reg_Names[register])
    inst["Source"] = set(regs)

    return inst


def categorise_jump_inst(inst):
    '''Classify a jump instruction, returns cond_branch or jump '''

    foundcat = 'OTHER'

    if ("c." in inst or "l." in inst):
        inst = inst[2:]

    for category, ptn in jump_categories:
        if ptn.match(inst):
            foundcat = category
            break
    return foundcat



def categorise_inst(inst):
    '''Classify a instructon into either load, alu etc '''

    foundcat = 'OTHER'

    if ("c." in inst or "l." in inst):
        inst = inst[2:]

    for category, ptn in categories:
        if ptn.match(inst):
            foundcat = category
            break
    return foundcat

def unroll_reg(reg_pattern):
    '''Retrun a list of unrolled regs for a given string e.g s0-s2 '''
    if ('-' in reg_pattern):
        reg_begin = ABI_Reg_Names.index(reg_pattern.split('-')[0])
        reg_end = ABI_Reg_Names.index(reg_pattern.split('-')[1])+1
        return ABI_Reg_Names[reg_begin:reg_end]
    else:
        if (isinstance(reg_pattern,str)):
            return [reg_pattern]
        else:
            return reg_pattern

def roll_regs(reg_pattern):
    '''Retrun a list of rolled regs '''
    regs = {}
    output = ""
    for reg in reg_pattern:
        if Categories_Reg(reg) not in regs:
            regs[Categories_Reg(reg)] =  [reg]
        else:
            regs[Categories_Reg(reg)].append(reg)
    for cat in regs:
        sorted_regs = sorted(regs[cat],key = lambda reg : int(Reg_Names[reg][1:]))
        if (cat =="Special"):
            output = output + ",".join(sorted_regs)
        else:
            previous = 0
            for i,reg in enumerate(sorted_regs):
                if int(reg[1:]) > previous+1 or i==0:
                    if (sorted_regs[i-1] not in output and i>0):
                        output = output +sorted_regs[i-1]+","+ reg 
                    else:
                        output = output +","+ reg 
                elif int(reg[1:]) == previous+1 and output[-1]!="-":
                    output = output + "-"
                if (i==len(sorted_regs)-1 and reg not in output):
                    output = output + reg
                previous = int(reg[1:])
    return(output)


def print_counter(cnt,fd = None,line_end="\n"):
    ''' 
        Outputs CSV formatted Python counter value either to Stdout or to a file handler ! 
    '''
    for entry in cnt.most_common():
        if (fd is None):
            print(entry[0], ",",entry[1],end=line_end)
        else:
            fd.write(str(entry[0])+","+str(entry[1])+line_end)
    print()

def immediate_coverage(offsets_frequency,signdness,number_of_bits):

    coverage_total = sum(offsets_frequency.values())         
    coverage = [ [0,coverage_total] for x in range(number_of_bits+1)]
    coverage[0][0] = offsets_frequency[0]
             
    if (signdness == "unsigned"):  
        for i in range(1,number_of_bits+1):
            for offset in offsets_frequency:
                if(offset >= (2**(i-1)) and offset < (2**i)):
                    coverage[i][0] +=  offsets_frequency[offset]
    elif (signdness == "signed"):
        for i in range(1,number_of_bits+1):
            for offset in offsets_frequency:
                if((offset >= (2**(i-2)) and offset < (2**(i-1))) or (offset >= (-2**(i-1)) and offset < (-2**(i-2))) ):
                    coverage[i][0] +=  offsets_frequency[offset]
    
    return coverage


def fit_in_field(offset,signedness,i):
    if (signedness == "unsigned" and offset < 0):
        return False
    else:
        s_offset = offset + 1 if (offset < 0 and signedness == "signed") else offset
        bitlen = 1 + s_offset.bit_length() if (signedness == "signed") else s_offset.bit_length()
        return (bitlen <= i)

def Searchset(required_set,search_space): 
    Set_Found = False
    Wasted_ops = 0
    for current_set in search_space:
        if (len(required_set - current_set) == 0):
            Set_Found = True
            Wasted_ops = (current_set - required_set)
            break
    return (current_set,Set_Found,Wasted_ops)

def number_of_required_bits(number,signedness):
    ''' Returns the number of bits required  to fit a number, if a number is a negative and we are trying to fit it in 
    an unsigned field, then we return None '''
    if (signedness == "unsigned" and number < 0):
        return None
    else:
        s_offset = number + 1 if (number < 0 and signedness == "signed") else number
        bitlen = 1 + s_offset.bit_length() if (signedness == "signed") else s_offset.bit_length()
        return bitlen

def generate_jump_instructions (msr_address,PC,linkregister = None):

    delta = msr_address - PC
    if (linkregister == None):
        if(fit_in_field(delta,"signed",12)):
            return [{"Instruction":"c.j","WoE":16,"Target_address":delta}]
        elif (fit_in_field(delta,"signed",21)):
            return [{"Instruction":"j","WoE":32,"Target_address":delta}]
        else:
            auipc_address = (msr_address&0xfffff000 >> 12)
            jal_address = (msr_address&0xfff)
            return [{"Instruction":"auipc","WoE":32,"Target_address":auipc_address},{"Instruction":"j","WoE":32,"Target_address":jal_address}]
    else:
        if (linkregister == "ra" and fit_in_field(delta,"signed",12)):
            return [{"Instruction":"c.jal","WoE":16,"Target_address":delta}]
        elif (fit_in_field(delta,"signed",21)):
            return [{"Instruction":"jal","WoE":32,"Target_address":delta}]
        else:
            auipc_address = (msr_address&0xfffff000 >> 12)
            jal_address = (msr_address&0xfff)
            return [{"Instruction":"auipc","WoE":32,"Target_address":auipc_address},{"Instruction":"jal","WoE":32,"Target_address":jal_address}]
    
