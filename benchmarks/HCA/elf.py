__author__ = "Ibrahim Abu Kharmeh"
__copyright__ = "Copyright 2021, Huawei R&D Bristol"
__license__ = "BSD 2-Clause"
__version__ = "0.4.0"



import sys
import os
import subprocess
import re 
from  collections import Counter
import traceback
import utils
import bisect
from math import ceil




class elf:
    ''' When this class is initialised, it opens an elf file with objdump, and retrieve the symbol table as well as disassembly. 
    If function list was passed using funcs_name, then we only analyse and retrive the disassembly of the given functions  '''

    def retrieve_function_name (self,pc_decimal):
        ''' 
        Return the name of the function which starts with a given addresses
        '''
        for function in self.func_bound_dict:
            if (self.func_bound_dict[function]["start"] == pc_decimal):
                return function.split('/')[1]
        for function in self.aux_func:
            if (function == pc_decimal):
                return self.aux_func[function]

    def retrieve_function_address (self,funcname):
        ''' 
        Return the name of the function which starts with a given addresses
        '''
        for function in self.func_bound_dict:
            if (funcname in function):
                return self.func_bound_dict[function]["start"]

    def retrieve_function_limit (self,pc_decimal,mode=0):
        ''' 
        Return the name of the function which the given addresses is within 
        '''
        # TODO The following changes the linear search to binary search, everything seems to work correctly, 
        # Just needs a bit of cleaning 
        index = bisect.bisect(self.func_bound_begin[1],pc_decimal)
        if (self.func_bound_begin[1][index-1] <= pc_decimal and self.func_bound_begin[2][index-1] >= pc_decimal):
            return self.func_bound_begin[0][index-1].split('/')[1] if (mode == 0) else self.func_bound_begin[0][index-1]
        elif(index != len(self.func_bound_begin[0])):
            self.dprint("Binary Search failed finding correct candidate for function name at PC",hex(pc_decimal),self.filepath,colour="red")
            return None

    def append(self, addendum):
        self.func.update(addendum.func)
        # self.func_bound_dict.update(appendum.func_bound_dict)

        for function in addendum.func_bound_dict:
            ammended_func_name = ((hex(int(function.split("/")[0],16)+self.endaddress))[2:].zfill(8)+"/"+function.split("/")[1])
            self.func_bound_dict[ammended_func_name] = {"start":addendum.func_bound_dict[function]["start"]+self.endaddress,"end":addendum.func_bound_dict[function]["end"]+self.endaddress}
            self.func_bound_begin[0].append(ammended_func_name)
            self.func_bound_begin[1].append(self.func_bound_dict[ammended_func_name]["start"])
            self.func_bound_begin[2].append(self.func_bound_dict[ammended_func_name]["end"])
            # self.func_bound_begin =

        for function in addendum.main_dictionary:
            ammended_func_name = ((hex(int(function.split("/")[0],16)+self.endaddress))[2:].zfill(8)+"/"+function.split("/")[1])
            self.main_dictionary[ammended_func_name] = {}

            for pc_decimal in addendum.main_dictionary[function]:
                self.main_dictionary[ammended_func_name][pc_decimal+self.endaddress] = addendum.main_dictionary[function][pc_decimal]

            for pc_decimal in self.main_dictionary[ammended_func_name]:
                self.main_dictionary[ammended_func_name][pc_decimal]["PC"] = hex(int(self.main_dictionary[ammended_func_name][pc_decimal]["PC"],16)+self.endaddress)[2:]
                if ("Target_address" in self.main_dictionary[ammended_func_name][pc_decimal]):
                    self.main_dictionary[ammended_func_name][pc_decimal]["Target_address"] += self.endaddress
                
        self.endaddress = pc_decimal + int(self.main_dictionary[ammended_func_name][pc_decimal]['WoE']/8)



    def __init__(self, filepath,pwd,verbosity=0,section = None):
        self.filepath = filepath
        funcs_name = []
        self.xlen = 0
        self.rodata = 0
        self.gp = None
        self.tp = None
        self.endaddress = 0
        objdump_para = ['riscv32-unknown-elf-objdump', '-t', '-T','-d', filepath]
        if section is not None:
            objdump_para.insert(1,"-j")
            objdump_para.insert(2,section)

        try:
            objdump = subprocess.Popen(objdump_para,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,cwd=pwd)
        except FileNotFoundError:
            print("Error: RISCV-32 Objdump not found")
            return

        shellpipe, stderr = objdump.communicate()

        if stderr is not None:
            print("Objdump is unable to decode the file used")
            self.init = False
            return
        else:
            self.init = True

        shell_response = shellpipe.decode("utf-8")

        self.symboltable = True
        self.main_dictionary = {}
        self.sections = []
        self.func = {}
        self.aux_func = {}
        self.func_bound_dict = {}
        self.func_bound_begin = [[],[],[]]
        self.other_list = {}
        self.aux_dictionary = {}
        self.ignored_functions = []
        
        # Parse the output of objdump and get the functions from the symbol table
        shell_response_list = shell_response.split('\n')

        for cline, line in enumerate(shell_response_list):
            lparameter = line.split()
            if ("file format" in line):
                if ("32" in line):
                    self.xlen = 32
                elif ("64" in line):
                    self.xlen = 64
                else:
                    raise AssertionError ("Unable to detrmine XLEN !")
                break

        # Parse the static symbol table
        for cline, line in enumerate(shell_response_list[cline:]):
            lparameter = line.split()
            if (line.startswith("DYNAMIC SYMBOL TABLE")):
                break
            elif ("no symbols" in line):
                self.symboltable = False
            elif (len(lparameter) > 5 and lparameter[2] == 'F'):
                if (lparameter[5] == ".hidden"  and (len(funcs_name) == 0 or lparameter[6] in funcs_name)):
                    self.func[lparameter[0]+"/"+lparameter[6]] = lparameter[4]
                elif (len(funcs_name) == 0 or lparameter[5] in funcs_name):
                    # Hack around LLVM13 not assigning len correctly for msave_restore funcs 
                    if (lparameter[5].startswith("__riscv") and int(lparameter[4]) == 0) : lparameter[4] = "999"
                    # Assign the value for bound check 
                    self.func[lparameter[0]+"/"+lparameter[5]] = lparameter[4]
            elif (len(lparameter) > 5 and lparameter[5].startswith("__riscv")):
                self.aux_func[int(lparameter[0],16)] = lparameter[5]
                
        # Parse the Dynamic symbol table
        for cline2, line in enumerate(shell_response_list[cline:]):
            lparameter = line.split()
            if (line.startswith("Disassembly of section")):
                break
            elif (len(lparameter) > 5 and lparameter[2] == 'DF'):
                if (len(funcs_name) == 0 or lparameter[2] in funcs_name and lparameter[0] != "0000000000000000"):
                    self.func[lparameter[0]+"/"+lparameter[6]+"@@"+lparameter[5]] = lparameter[4]
        # Dict that replaces the bigger and smaller sign with None, used for target addressed parsing !
        translate_dic = {0x3A:None, 0x3C: None,0x3E: None}
        #Parse PLT section 
        plt_index = "First"
        if (line == "Disassembly of section .plt:"):
            for cline3, line in enumerate(shell_response_list[cline+cline2+1:]):
                lparameter = line.split()
                if (line == ''):
                    continue
                elif (line.startswith("Disassembly of section")):
                    break
                elif (len(lparameter) == 2):
                    if (funcs_name is None or lparameter[1].translate(translate_dic) in funcs_name):
                        self.func[lparameter[0]+"/"+lparameter[1].translate(translate_dic)] = lparameter[0]
                        if (plt_index != "First"):
                            self.func[plt_index] = hex(int(shell_response_list[cline+cline2+1+cline3-2].split(":")[0].strip(),16) - int(self.func[plt_index],16) )
                        plt_index = lparameter[0]+"/"+lparameter[1].translate(translate_dic)


        self.verbosity = verbosity
        self.disassembly = shell_response_list[cline2+cline:]

    def calculate_exec_size(self):
        try:
            readelf = subprocess.Popen(
            ["readelf"] + ["-t", self.filepath], stdout=subprocess.PIPE)
        except FileNotFoundError:
            print("Error: readelf not found")
            return
        out, err = readelf.communicate()
        totalsize = 0
        if (err is None):
            elfread_res = out.decode('utf-8').split('\n')
            for i in range(0, len(elfread_res), 3):
                if (self.verbosity >1):
                    print(elfread_res[i:i+3])
                elfsection = elfread_res[i:i+3]
                try:
                    if (elfsection[2].endswith("ALLOC, EXEC")):
                        section_size = elfsection[1].split()
                        totalsize += int(section_size[3], 16)
                except IndexError:
                    break

        return totalsize

    def read_elf_sections(self):
        try:
            readelf = subprocess.Popen(
            ["readelf"] + ["-a", self.filepath], stdout=subprocess.PIPE)
        except FileNotFoundError:
            print("Error: readelf not found")
            return
        out, err = readelf.communicate()
        if (err is None):
            elfread_res = out.decode('utf-8').split('\n')
            for cline,line in enumerate(elfread_res):
                if line.startswith("Section Headers"):
                    break
            for cline,line in enumerate(elfread_res[cline+2:]):
                if line.startswith("Key to Flags"):
                    break
                else:
                    line = line.split("]")[1].split()
                    if (len(line) > 1 and line[1] in ["PROGBITS", "NOBITS"]):
                        self.sections.append({"Section":line[0],"Address":int(line[2],16),"Offset":int(line[3],16),"Size":int(line[4],16),"Alignment":int(line[-1])})
        

    
    def print_dict(self):
        ''' 
        Print the whole Dictionary 
        '''
        for function in sorted(self.main_dictionary):
            print(function)
            for pc_decimal in sorted(self.main_dictionary[function]):
                print(self.main_dictionary[function][pc_decimal])

    def num_of_funcs(self):
        '''
        Return the number of functions in the dictionary 
        '''
        return (len(self.main_dictionary))


    def iterate_dict(self):
        for iter in self.main_dictionary:
            yield iter

# To print parts of the main_dictionary
    def print_options(self,options):
        for function in sorted(self.main_dictionary):
            print(function)
            for pc_decimal in sorted(self.main_dictionary[function]):
                console_tell = 0
                for option in options.split():
                    if (option in self.main_dictionary[function][pc_decimal]):
                        print("".join(self.main_dictionary[function][pc_decimal][option]),end=" ")
                        console_tell = console_tell +1
                if (console_tell > 0):
                        print("")      
                        
    
    def retrieve_field(self,req_instructions = [],req_cat= None, options = None, exact = False,woe_insensitive=False,additional_condition = lambda unused: True):
        '''
        Used to retreive a list of options from the main dictionary for a given instruction, or a given category
        If exact is set true, it will only return the instruction if an exact match was found to the given options
        '''

        instructions = list()
        if (req_cat is None and req_instructions is None):
            raise AssertionError('Retrieve_field requires either category or instruction along with a list of fields')
        for function in sorted(self.main_dictionary):
            for pc_decimal in sorted(self.main_dictionary[function]):
                if ("Instruction" not in self.main_dictionary[function][pc_decimal]):
                    continue
                else:
                    current_instruction = self.main_dictionary[function][pc_decimal]["Instruction"][2:] if (woe_insensitive and "c." in self.main_dictionary[function][pc_decimal]["Instruction"]) else self.main_dictionary[function][pc_decimal]["Instruction"]

                if ((current_instruction in req_instructions or self.main_dictionary[function][pc_decimal]["Category"] == req_cat) and additional_condition(self.main_dictionary[function][pc_decimal])):
                    if (options == None):
                       instructions.append(self.main_dictionary[function][pc_decimal])
                    else:
                        instruction = {}
                        instruction["Instruction"] = self.main_dictionary[function][pc_decimal]["Instruction"]
                        for option in options:
                            if (option in self.main_dictionary[function][pc_decimal]):
                                instruction[option] = self.main_dictionary[function][pc_decimal][option]
                        if ((exact and len(instruction)-1 == len(options)) or not exact):
                            instructions.append(instruction.copy())

        return instructions

    def retrieve_insts(self,req_cat= None):
        '''
        Used to retrieve all instructions used, or retrieve all instructions that match a given category 
        '''

        instructions = list()
        for function in sorted(self.main_dictionary):
            for pc_decimal in sorted(self.main_dictionary[function]):
                # Make sure that the current entry contains a processed instruction, otherwise proceed to the next entry ! 
                if ("Instruction" not in self.main_dictionary[function][pc_decimal]):
                    continue
                # If no caterory is provided, then return all the instructions, otherwise return anything matches that category
                elif (req_cat is None):
                    instructions.append(self.main_dictionary[function][pc_decimal]["Instruction"])
                elif (self.main_dictionary[function][pc_decimal]["Category"] == req_cat):
                    instructions.append(self.main_dictionary[function][pc_decimal]["Instruction"])
        return instructions


    def calculate_dict_size(self,req_functions= None,mode=0):
        '''
        Used to calculate the size of a given list of functions or the complete dictionary
        '''

        complete_size = 0
        list_size = dict()
        for function in sorted(self.main_dictionary):
            for pc_decimal in sorted(self.main_dictionary[function]):
                # Make sure that the current entry contains a processed instruction, otherwise proceed to the next entry ! 
                if ("Instruction" in self.main_dictionary[function][pc_decimal]):
                    if(req_functions is None and mode == 0): 
                        complete_size += self.main_dictionary[function][pc_decimal]['WoE']
                    elif(req_functions is None and mode == 1): 
                        if (function in list_size):
                            list_size[function] += (self.main_dictionary[function][pc_decimal]['WoE']/8)
                        else:
                            list_size[function] = (self.main_dictionary[function][pc_decimal]['WoE']/8)
                    elif (self.main_dictionary[function][pc_decimal]["Instruction"] in req_functions):
                        complete_size += self.main_dictionary[function][pc_decimal]['WoE']
                        
                
        if (mode == 0):
            return (complete_size/8)
        else:
            return list_size

    def add_ro_data(self,len):
        self.rodata = self.rodata + len


    def construct_main_dict(self,parse_all=False):
        ''' 
        Parse the file disassembly and convert it to a itertable dictionary 
        '''

        function = ""
        HOBS_TO_MARK = list()
        caddress = 0 
        for line in self.disassembly:
            line = line.split()
            if (len(line) < 2):
                continue
            else:
                if (line[1][-1] == ":"):  
                    pc = line[0]
                else:
                    pc = line[0][0:-1]

            if (utils.hexadecimal_ptn.match(pc) == None):
                continue
            

            pc_decimal = int(pc, 16)
            operands = ""
            inst=""
            # If the line contains a new function name, then create a new function entry in the 
            if len(line) > 1 and line[1][-1] == ":":
                function = line[0]+"/"+line[1][1:-2]
                # Init an empty dict for a given function if this is the first time we see it (OTHERWISE it may be second encounter of static declaration !)
                if (function not in self.main_dictionary): 
                    self.main_dictionary[function] = {}
                self.main_dictionary[function][pc_decimal] = {'PC': pc,'HOB': True}
            # Otherwise, check if its a valid instruction 
            elif line[0][-1] == ":":
                if function in self.func or parse_all:              

                    # If no static symbol table, then don't bound check for now !! 
                    if ( parse_all == False and self.symboltable == True and (pc_decimal >  (int(function.split('/')[0],16) + int (self.func[function], 16)))):
                        continue
    
                    if pc_decimal not in self.main_dictionary[function]:
                        self.main_dictionary[function][pc_decimal] = {}
                    self.main_dictionary[function][pc_decimal]['PC'] = pc

                    
                    if len(line) > 4 and (line[4] == "l.li" or line[4][0:2] == '0x'):
                        line = [line[0]] + [''.join(line[1:4])] + line[4:]

                    # locate junk
                    if len(line) > 2 and (line[2][0:2] == '0x' or line[2] == 'unimp'):
                        continue

                    # categorize the fields
                    elif len(line) > 2 and utils.hexadecimal_ptn.match(line[1]) and not (utils.hexadecimal_ptn.match(line[2]) and len(line[2]) == 8):
                        inst = line[2]
                        if len(line) > 3:
                            operands = line[3].split(',')
                                        
                        if(self.verbosity > 0):
                            self.main_dictionary[function][pc_decimal]['Debug'] = inst +" "+",".join(operands)
                        
                        self.main_dictionary[function][pc_decimal]['Encoding'] = line[1]
                        woe = 4 * len(line[1])

                        self.main_dictionary[function][pc_decimal]['WoE'] = woe

                        category = utils.categorise_inst(inst)
                        caddress = pc_decimal if (pc_decimal > caddress) else caddress

                        self.main_dictionary[function][pc_decimal]['Instruction'] = "c."+inst if (woe == 16 and inst[0:2] != "c.") else  inst
                        self.main_dictionary[function][pc_decimal]['Category'] = category

                        if category in ['branch', 'jump', 'jump_imm']:
                            self.main_dictionary[function][pc_decimal]['HOB'] = True
                            if ((len(line) > 3 and inst != 'jalr' and inst != 'jr') or (len(line) == 7) ):
                                branch_pc_decimal = int(line[5], 16) if (len(line) == 7) else int(operands[-1], 16) 
                                if (branch_pc_decimal in self.main_dictionary[function]):
                                    self.main_dictionary[function][branch_pc_decimal]['HOB'] = True
                                else:
                                    HOBS_TO_MARK.append(branch_pc_decimal)
                                self.main_dictionary[function][pc_decimal]['Target_address'] = branch_pc_decimal
                            # Handle compressed instructions (implicit destination register) and single operand jal,jalr,jr
                            if ((len(operands[0:-1]) == 0)):
                                if (inst == 'jal' and woe == 16):
                                    self.main_dictionary[function][pc_decimal]['Destination'] = ("ra",)
                                elif(inst == 'jalr' and woe == 16):
                                    self.main_dictionary[function][pc_decimal]['Source'] = [operands[0]]
                                    self.main_dictionary[function][pc_decimal]['Destination'] = ("ra",)
                                elif ((inst in ['jr','jalr']) and "(" in operands[0]):
                                    self.main_dictionary[function][pc_decimal]['Source'] = [operands[0].split('(')[1][:-1]]                                 
                                    self.main_dictionary[function][pc_decimal]['Destination'] =  ("zero",)
                                elif (inst in ['jr','jalr']):
                                    self.main_dictionary[function][pc_decimal]['Source'] = [operands[0]]
                                    self.main_dictionary[function][pc_decimal]['Destination'] =  ("zero",)
                                elif (inst == 'j'):
                                    self.main_dictionary[function][pc_decimal]['Destination'] =  ("zero",)                                  
                                elif (inst != 'ret'):
                                    print(line)
                                    raise AssertionError("Encountered an unexpected branch instruction")

                            # When we have destination register and source register ! 
                            elif (len(operands[0:-1]) == 1):
                                # Assign the Destination_register
                                if(inst == 'jal' or inst == 'jalr'):
                                    self.main_dictionary[function][pc_decimal]['Destination'] = (operands[0],)
                                # Assign the Source register
                                if (inst == 'jalr'):
                                    if ("(" in operands[1]):
                                        self.main_dictionary[function][pc_decimal]['Source'] = [operands[1].split('(')[1][:-1]]
                                    else:
                                        self.main_dictionary[function][pc_decimal]['Source'] = [operands[1]]

                                elif (inst != 'jal'):
                                    self.main_dictionary[function][pc_decimal]['Source'] = [operands[0]]
                            # Append the operands of the jump (one or two operands for the jump )   (SB Type Instructions)
                            elif (len(operands[0:-1]) > 1):
                                self.main_dictionary[function][pc_decimal]['Source'] = tuple(operands[0:-1])
                            
                            
      
                        elif category == 'OTHER':
                            if inst not in self.other_list:
                                self.other_list[inst] = inst
                            # for inst in sorted(other_list):
                                if (self.verbosity>1):
                                    print("Objdump passed an instruction "+inst+ " that we don't know how to handle "+ " ".join(line))
                        # If we reached here, then surely it means its an identified instruction that is not flow control ! 
                        elif category == 'system':
                            if (inst == 'csrw'):
                                self.main_dictionary[function][pc_decimal]['Source'] = operands[1:]
                            elif (inst == 'csrwi'):
                                self.main_dictionary[function][pc_decimal]['Immediate'] = operands[1:]
                        elif category == "multiple":
                            if (re.search("{(.*)}",line[3]) is not None):
                                if ("-" in line[3].split("}")[0]):
                                    rolled_registers = re.search("{(.*)}",line[3]).group(1).split(",")
                                    unrolled_register = [rolled_registers[0]]
                                    unrolled_register.extend(utils.unroll_reg(rolled_registers[1]))
                                else:
                                    unrolled_register = re.search("{(.*)}",line[3]).group(1).split(",")
                                
                            else:
                                raise AssertionError(" ".join(line)+self.filepath)

                            if (inst == "pop" or inst == "popret"):                               
                                self.main_dictionary[function][pc_decimal]['Destination'] = tuple(unrolled_register)
                                self.main_dictionary[function][pc_decimal]['Immediate'] = int(operands[-1]) 
                            elif (inst == "push"):
                                self.main_dictionary[function][pc_decimal]['Source'] =  tuple(unrolled_register)
                                self.main_dictionary[function][pc_decimal]['Immediate'] = int(operands[-1]) 

                        elif category == "alu_imm": 
                            self.main_dictionary[function][pc_decimal]['Destination'] = (operands[0],)
                            self.main_dictionary[function][pc_decimal]['Source'] = (operands[1],)
                            self.main_dictionary[function][pc_decimal]['Immediate'] = operands[2]
                        elif category == "load_imm":
                            self.main_dictionary[function][pc_decimal]['Destination'] = (operands[0],)
                            self.main_dictionary[function][pc_decimal]['Immediate'] = operands[1]
                        elif category == "store":
                            self.main_dictionary[function][pc_decimal]['Source'] = (operands[0],operands[1].split('(')[1][:-1],)
                            self.main_dictionary[function][pc_decimal]['Immediate'] = operands[1].split('(')[0]
                            if(len(line) > 4):
                                self.main_dictionary[function][pc_decimal]['Address']  = line[5]
                        elif category == "load":
                            self.main_dictionary[function][pc_decimal]['Destination'] = (operands[0],)
                            self.main_dictionary[function][pc_decimal]['Immediate'] = operands[1].split('(')[0]
                            self.main_dictionary[function][pc_decimal]['Source'] = (operands[1].split('(')[1][:-1],)
                            if(len(line) > 4):
                                self.main_dictionary[function][pc_decimal]['Address']  = line[5]

                        elif (len(operands)>0):
                            self.main_dictionary[function][pc_decimal]['Destination'] = (operands[0],)
                            if (len(operands)>1):         
                                if '(' in operands[1]:
                                    self.main_dictionary[function][pc_decimal]['Immediate'] = operands[1].split('(')[0]
                                    self.main_dictionary[function][pc_decimal]['Source'] = (operands[1].split('(')[1][:-1],)
                                else:
                                    self.main_dictionary[function][pc_decimal]['Source'] = tuple(operands[1:])
                else:
                    if (function not in self.ignored_functions):
                        self.ignored_functions.append(function)
                        if (self.verbosity > 1):
                            print("Function was not parsed " + function)
            else:
                raise AssertionError('Line does not match expected input'+" ".join(line))


        # Create dictionary contains boundary PC of functions
        for function in sorted(self.main_dictionary, key = lambda x: int(x.split("/")[0],16)):
            self.func_bound_dict[function] = {}
            pc_keylist = sorted(self.main_dictionary[function].keys())
            self.func_bound_dict[function]['start'] = int(pc_keylist[0])
            self.func_bound_dict[function]['end'] = int(pc_keylist[-1])
            self.func_bound_begin[0].append(function)
            self.func_bound_begin[1].append(int(pc_keylist[0]))
            self.func_bound_begin[2].append(int(pc_keylist[-1]))

        # Pass through the dict and marks HOBs in their prospective locations
        for HOB in HOBS_TO_MARK:
            target_func = self.retrieve_function_limit(HOB,1)
            if (target_func == None or target_func in self.aux_func.values()):
                continue
            try:
                self.main_dictionary[target_func][HOB]["HOB"] = True
            except KeyError:
                self.dprint("HOB at unparsed function", HOB,colour="red")
            # TODO return a meaningfull return code !

        #  Assign the end address of this dictionary !
        funcname = self.retrieve_function_limit(caddress,1)
        self.endaddress = caddress + int(self.main_dictionary[funcname][caddress]['WoE']/8)
        return True
    


    def get_whole_inst(self,function, pc_decimal):
            return self.main_dictionary[function][pc_decimal]


    def get_mnemonic(self,function, pc_decimal):
        return self.main_dictionary[function][pc_decimal]['Instruction']

    def add_store_label(self,tar_inst, pc, label):
        if pc not in self.aux_dictionary:
            self.aux_dictionary[pc] = {}
        if tar_inst not in self.aux_dictionary[pc]:
            self.aux_dictionary[pc][tar_inst] = {}

        if 'Store Label' in self.aux_dictionary[pc][tar_inst]:
            self.aux_dictionary[pc][tar_inst]['Store Label'].append(label)
        else:
            self.aux_dictionary[pc][tar_inst]['Store Label'] = [label]

    def find_source_dependencies(self,mode,target_inst=None, req_cat=None, woe_insensitive=False,traverseback=True,pass_through = lambda unused: False,additional_condition = lambda unused: True):

        '''
        Find the source dependencies of a given target instruction target_inst
        Options: 
        if mode is 0, the instruction along with the operands are returned, otherwise only the instruction is returned
        Kill at branch is currently unused
        Kill at arithmetic would continue tracking if an instruction get overwitten by a constant instruction !! Only usefull for tracking L.LI inferences 
        woe_insensitive, match the target instrcution regardless if its compressed, long or normal
         '''
        
        if mode == 0:
            get_inst = self.get_whole_inst
        elif mode == 1:
            get_inst =  self.get_mnemonic

        if (req_cat is None and target_inst is None):
            raise AssertionError('find_source_dependencies requires either category or instruction')
        elif (req_cat is None and len(target_inst)==1):
            track_branch = (utils.categorise_jump_inst(target_inst[0]) != "OTHER")
        else:
            track_branch = False
            
        li_reg_list = set()
        reg_inst_dict = []
        src_ints = {}
        

        for function in sorted(self.main_dictionary):
            f_instructions_addresses = sorted(self.main_dictionary[function],reverse=traverseback)
            for f_offset,pc_decimal in enumerate(f_instructions_addresses):
                if 'Instruction' in self.main_dictionary[function][pc_decimal]:
                    # Search for the instruction we are tracking their sources, and add the sources to the tracking list
                    inst = self.main_dictionary[function][pc_decimal]['Instruction']
                    if ( ((target_inst is not None and (inst in target_inst or (woe_insensitive and "c." in inst and inst[2:] in target_inst))) 
                        or (req_cat is not None and utils.categorise_inst(inst) == req_cat)) and additional_condition(self.main_dictionary[function][pc_decimal])):
                        if 'Source' in self.main_dictionary[function][pc_decimal]:
                            last_matched_inst = self.main_dictionary[function][pc_decimal]
                            for reg in self.main_dictionary[function][pc_decimal]['Source']:
                                li_reg_list.add(reg)
                                if reg in src_ints:
                                    src_ints[reg].append(self.main_dictionary[function][pc_decimal])
                                else:
                                    src_ints[reg] = [self.main_dictionary[function][pc_decimal]]
                        else:
                            raise AssertionError ("Instruction without prerequisite fields!")
                        # Skip the checks for HOB if we are tracking cond branches and the current instruction equals tracked intruction
                        if (track_branch and utils.categorise_jump_inst(inst) != "OTHER"):
                            continue
                    # If the tracking list contains any registers, then see if they are written by the current instruction ! 
                    if len(li_reg_list) > 0:
                        li_used_list = []
                        for li_reg in li_reg_list:
                            # TODO make sure that swapping the order of the if clause does not have any other side effects !!
                            if (('Destination' in self.main_dictionary[function][pc_decimal] and li_reg in self.main_dictionary[function][pc_decimal]['Destination'] and 
                                last_matched_inst != self.main_dictionary[function][pc_decimal])):
                                reg_inst_dict.append([get_inst(function, pc_decimal)]+src_ints[li_reg])
                                li_used_list.append(li_reg)
                                
                            if ('HOB' in self.main_dictionary[function][pc_decimal] and f_offset != (len(self.main_dictionary[function])-1)):
                                # unclear_regs.append(src_ints)
                                #  FIXME, with the current construction of this function, sometimes we would ignore 
                                # a tangling instruction behind a HOB !! 
                                # Change the following to a list comprenhension
                                li_used_list = list(set(li_used_list+list(li_reg_list)))
                                break
                            else:
                                pass
                        for del_reg in li_used_list:
                            del src_ints[del_reg]
                            li_reg_list.remove(del_reg)



        return reg_inst_dict

    def find_dependant_insts_from(self, mode, starting_inst, woe_insensitive=False,pass_through = lambda unused: False):
        pc = int(starting_inst["PC"], 16)
        function_name = self.retrieve_function_limit(pc_decimal=pc, mode=1)
        function = sorted(self.main_dictionary[function_name])
        destination_register = self.main_dictionary[function_name][pc]['Destination'][0]
        dependant_instruction = []
        for pc_decimal in function[function.index(pc)+1:]:
            if ('Destination' in self.main_dictionary[function_name][pc_decimal] and 
                destination_register in self.main_dictionary[function_name][pc_decimal]['Destination'] and pass_through(self.main_dictionary[function_name][pc_decimal])):
                return dependant_instruction
            elif "HOB" in self.main_dictionary[function_name][pc_decimal]:
                if ('Target_address' in self.main_dictionary[function_name][pc_decimal] and self.main_dictionary[function_name][pc_decimal]['Target_address'] > function[-1]):
                    jump_out_flag = True
                else:
                    jump_out_flag = False

                if (destination_register[0] == "a" or destination_register[0] == "t" and jump_out_flag == True):
                    return dependant_instruction
                else:
                    return []
            elif "Source" in self.main_dictionary[function_name][pc_decimal]:
                for src in self.main_dictionary[function_name][pc_decimal]["Source"]:
                    if src in destination_register:
                        dependant_instruction.append(
                            self.main_dictionary[function_name][pc_decimal])
                        break

    def calculate_gp(self):
        # Calculate existing GP location
        gp_lw = self.retrieve_field(req_instructions=["lw"],additional_condition=(lambda entry: "Address" in entry and "gp" in entry["Source"]))
        if (len(gp_lw) > 0):
            self.gp = int(gp_lw[0]["Address"],16)-int(gp_lw[0]["Immediate"])

    def find_dependant_insts(self,mode,target_inst='l.li', append_target_inst=False, woe_insensitive=False, kill_at_branch=True,
                            ignore_same_func_jump=True, functions=[],start_condition = lambda unused: True,pass_through = lambda unused: False):

        '''
        Find Instructions dependant on a given target instruction target_inst
        Options: 
        if mode is 0, the instruction along with the operands are returned, otherwise only the instruction is returned
        if append_target_inst is set, then the begining of the chain is appended to the result as well
        Kill at branch is currently unused
        pass_through would continue tracking if the passed lambda function returns true !! 
        woe_insensitive, match the target instrcution regardless if its compressed, long or normal
         '''
        
        if mode == 0:
            get_inst = self.get_whole_inst
        elif mode == 1:
            get_inst =  self.get_mnemonic

        inst_list = []
        li_reg_list = []
        never_used_list = []
        reg_inst_dict = {}
        
        last_target_instruction = {}


        jump_same = 0
        jump_out = 0


        for function in sorted(self.main_dictionary):
            reg = ""
            # Read a new instruction from the dict !
            for pc_decimal in sorted(self.main_dictionary[function]):
                jump_out_flag = False
                jump_same_flag = False
                if 'Instruction' in self.main_dictionary[function][pc_decimal]:
                    # Retrive the instruction name for the given PC value ! 
                    inst = self.main_dictionary[function][pc_decimal]['Instruction']
                    # If we have at least 1 register is written/loaded by target_inst and hasn't been used
                    if len(li_reg_list) > 0:
                        li_used_list = []
                        for li_reg in li_reg_list:
                            # If the written/loaded reg is used, store the inst which uses it as (reg, [inst]) K-V pair and remove it from the list
                            if (('Source' in self.main_dictionary[function][pc_decimal] and li_reg in self.main_dictionary[function][pc_decimal]['Source'])):
                                if (append_target_inst):
                                    reg_inst_dict[li_reg] = [last_target_instruction[li_reg],get_inst(function, pc_decimal)]
                                    del last_target_instruction[li_reg]
                                else:
                                    reg_inst_dict[li_reg] = [get_inst(function, pc_decimal)]
                                li_used_list.append(li_reg)
                                first_flag = True
                            elif 'Destination' in self.main_dictionary[function][pc_decimal] and li_reg in self.main_dictionary[function][pc_decimal]['Destination']:
                                never_used_list.append(li_reg)
                                li_used_list.append(li_reg)
                            else:
                                pass


                            if len(reg_inst_dict) == 0:
                                if utils.categorise_jump_inst(inst) == 'jumps':
                                    jump_pc = 0
                                    # FIXME the structure of source changed from a list that contain a list to source in case of branches !! 
                                    # For the existing type of branches, it think that the address would be stored in either target address or source ?
                                    if 'Target_address' in self.main_dictionary[function][pc_decimal]:
                                        jump_pc = self.main_dictionary[function][pc_decimal]['Target_address']
                                    elif ('Source' in self.main_dictionary[function][pc_decimal] and len(self.main_dictionary[function][pc_decimal]['Source']) > 0 
                                    and utils.hexadecimal_ptn.match(self.main_dictionary[function][pc_decimal]['Source'][0]) and len(self.main_dictionary[function][pc_decimal]['Source'][0]) > 3):
                                        jump_pc = int(
                                            self.main_dictionary[function][pc_decimal]['Source'][0], 16)
                                    else:
                                        pass
                                    # Filter out jumps out of the search scope ! 
                                    if not (jump_pc <= self.func_bound_dict[function]['end'] and jump_pc >= self.func_bound_dict[function]['start']):
                                        jump_out_flag = True
                                    else:
                                        jump_same_flag = True
                                        if ignore_same_func_jump:
                                            continue

                                    li_reg_list = []
                                    last_target_instruction = {}  
                                    break
                                elif utils.categorise_jump_inst(inst) == 'cond_branch' and kill_at_branch:
                                    li_reg_list = []
                                    last_target_instruction = {}  
                                    break

                            
                        li_reg_list = [n for n in li_reg_list if n not in li_used_list]

                    # When at least a K-V pair is found from above, and that reg hasn't been overwritten
                    if len(reg_inst_dict) > 0:
                        delete_reg_list = []
                        for reg in reg_inst_dict:

                            if ('HOB' in self.main_dictionary[function][pc_decimal]):
                                if (utils.categorise_jump_inst(inst) != "OTHER"):
                                    if 'Target_address' in self.main_dictionary[function][pc_decimal]:
                                        jump_pc = self.main_dictionary[function][pc_decimal]['Target_address']
                                        # Boundary Check when Jumping between functions, check if we are jumping in the same function or outside it 
                                        if (jump_pc <= self.func_bound_dict[function]['end'] and jump_pc >= self.func_bound_dict[function]['start']):
                                            jump_same_flag = True
                                        else:
                                            jump_out_flag = True
                                    elif (inst == "c.ret"):
                                        jump_out_flag = True

                                # FIXME How are going to handle conditional jump instructions !
                                if (utils.categorise_jump_inst(inst) == "jumps"):
                                    if ((reg[0] == "a" or reg[0] == "t" and jump_out_flag == True) or target_inst == "auipc"):
                                        inst_list.append(reg_inst_dict.get(reg))
                                    elif(self.verbosity > 1):
                                        print(reg,"Deleted because dont know how it will be handled after jump !")
                                    delete_reg_list.append(reg)
                                # Either conditional branch or branch target ! 
                                else:
                                    never_used_list.append(li_reg_list)
                                    li_reg_list = []
                                    delete_reg_list.append(reg)
                                    last_target_instruction = {}  
                            else:
                                # First flag is used to avoid double seeing first instruction !  
                                if not first_flag:
                                    if (('Source' in self.main_dictionary[function][pc_decimal] and reg in self.main_dictionary[function][pc_decimal]['Source'])):
                                        # new inst found which uses the written/loaded reg
                                        reg_inst_dict[reg].append(
                                            get_inst(function, pc_decimal))

                                if 'Destination' in self.main_dictionary[function][pc_decimal] and reg in self.main_dictionary[function][pc_decimal]['Destination']:
                                    if not (pass_through(self.main_dictionary[function][pc_decimal])):
                                        inst_list.append(reg_inst_dict.get(reg))
                                        delete_reg_list.append(reg)
   
                        for del_reg in delete_reg_list:
                            del reg_inst_dict[del_reg]
                    first_flag = False
                    # When find target_inst
                    if ((inst == target_inst or (woe_insensitive and "c." in inst and inst[2:] == target_inst)) and start_condition(self.main_dictionary[function][pc_decimal]) ):
                        # Either we have an arithmetic operation which would have a destination register which we save
                        if 'Destination' in self.main_dictionary[function][pc_decimal]:
                            li_reg_list.extend(self.main_dictionary[function][pc_decimal]['Destination'])
                            last_target_instruction[self.main_dictionary[function][pc_decimal]['Destination'][0]] = get_inst(function, pc_decimal)
                        # Or not, in which case we carry on to the next instruction 
                        else:
                            continue
                if jump_out_flag:
                    jump_out += 1
                if jump_same_flag:
                    jump_same += 1
            if li_reg_list != []:
                never_used_list.append(li_reg_list)
                li_reg_list = []

        return inst_list

    def dprint(self,*args,**kargs):
        limit = kargs["level"] if ("level" in kargs) else 1
        colours =  {"normal":'\033[0m',"yellow":'\033[93m',"red":'\033[91m'}
        msg_colour = kargs["colour"] if ("colour" in kargs) else "normal"
        if(self.verbosity >= limit):
            print(colours[msg_colour],*args,colours["normal"])


    def find_epilogue_prologue_lw_sw (self):
        stack_adj_push = list()
        stack_adj_pop = list()
        # Variables depending if compressed version is used or if normal version is used
        store_inst = "sw" if (self.xlen == 32) else "sd"
        load_inst = "lw" if (self.xlen == 32) else "ld"
        inst_match = lambda inst, target_inst : (("c." in inst and inst[2:] == target_inst) or inst == target_inst)
        Found_stack_adj = False
        # Scan program for stack adjustments and append!!
        for function in sorted(self.main_dictionary):
            # Make sure we are not counting the ones in msr routines ! 
            if ("__riscv_save" in function or "__riscv_restore" in function):
                continue
            for pc_decimal in sorted(self.main_dictionary[function]):
                current_entry = self.main_dictionary[function][pc_decimal]
                # If we see a new HOB, then make sure to disable writing to previous entry ! 
                if ("HOB" in current_entry):
                    Found_stack_adj = False
                # Scan instruction to find add negative stack adjustment as indication of begining of PUSH instruction 
                if ("Instruction" in current_entry and  inst_match(current_entry["Instruction"],"addi") 
                    and "sp" in current_entry["Source"] and "sp" in current_entry['Destination'] and "-" in current_entry["Immediate"]):
                    stack_adj_push.append({"Adj":current_entry, "Opt":[], "rcount_val":0,"Instruction":"","Embedded_moves":[]})
                    Found_stack_adj = True
                # Find all consecutive stack relative stores and assign them to last seen stack relative addi
                elif ("Instruction" in current_entry and  inst_match(current_entry["Instruction"],store_inst) and Found_stack_adj
                    and  current_entry["Source"][1] == "sp" and (utils.Categories_Reg(current_entry["Source"][0]) == "s" or current_entry["Source"][0] == "ra" )):
                    if (int(current_entry["Immediate"])+int(stack_adj_push[-1]["Adj"]["Immediate"]) < 0):
                        stack_adj_push[-1]["Opt"].append(current_entry)
                # NOTE For embedded moves, Tariq says this is not needed as compiler can in theory shuffle registers around to fit them !!
                #      current_entry['Destination'][0][1:] ==  current_entry["Source"][0][1:]
                elif ("Instruction" in current_entry and current_entry["Instruction"] in ["mv", "c.mv"]  and Found_stack_adj and len(stack_adj_push[-1]["Opt"])>0
                    and utils.Categories_Reg(current_entry['Destination'][0]) == "s" and utils.Categories_Reg(current_entry["Source"][0]) == "a"):
                    stack_adj_push[-1]["Embedded_moves"].append(current_entry)

            Found_stack_adj = False
            Found_Return = {"Ret":None,"Return_value":None}
            for pc_decimal in sorted(self.main_dictionary[function],reverse=True):
                current_entry = self.main_dictionary[function][pc_decimal]
                if ("Instruction" in current_entry and  inst_match(current_entry["Instruction"],"addi")  and "sp" in current_entry["Source"] 
                    and "sp" in current_entry['Destination'] and "-" not in current_entry["Immediate"]):
                    # If we detected ret before and didnt see any control flow discontinuities (new HOBs) add to existing entry, otherwise create new entry
                    stack_adj_pop.append({"Adj":current_entry, "Opt":[], "rcount_val":0,"Instruction":"","Ret":Found_Return})
                    Found_Return = {"Ret":None,"Return_value":None}
                    Found_stack_adj = True
                elif ("Instruction" in current_entry and Found_stack_adj and  inst_match(current_entry["Instruction"],load_inst)  
                     and current_entry["Source"][0] == "sp" and (utils.Categories_Reg(current_entry['Destination'][0]) == "s" or current_entry['Destination'][0] == "ra") 
                     and "Immediate" in stack_adj_pop[-1]["Adj"]):
                    if  (int(current_entry["Immediate"]) + int(stack_adj_pop[-1]["Adj"]["Immediate"]) > 0):
                        stack_adj_pop[-1]["Opt"].append(current_entry)
                elif ("Instruction" in current_entry and inst_match(current_entry["Instruction"],"ret")):
                    Found_stack_adj = False
                    Found_Return["Ret"],Found_Return["Return_value"] = current_entry,None
                elif ("Instruction" in current_entry and  current_entry["Instruction"] in ["li","c.li"] and 
                        current_entry['Destination'][0] == "a0"):
                    Found_Return["Return_value"] = current_entry
                    if (Found_stack_adj == True):
                        stack_adj_pop[-1]["Ret"]["Return_value"] = current_entry
                elif ("HOB" in current_entry):
                    Found_stack_adj = False
                    Found_Return = {"Ret":None,"Return_value":None}
                    # stack_adj_pop.append({"Adj":{}, "Opt":[],"Ret":current_entry, "rcount_val":0,"Instruction":""})
                # If we see a new HOB, then make sure to append new entry FIXME maybe this should be a flag instead of wasting memorey !
                

        return (stack_adj_push,stack_adj_pop)


    def emulate_msr_savings (self,both_encodings=False):
        m_save_routines = list()
        m_restore_routines = list()
        alist =  [set(["ra", "s0","s1","s2"]),set(["ra", "s0","s1","s2","s3","s4","s5","s6"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11"])]

        m_save_routines,m_restore_routines = self.find_epilogue_prologue_lw_sw()
        rfunction = {0:("__riscv_save_0", " __riscv_restore_0"),
                     1:("__riscv_save_4", " __riscv_restore_4"),
                     2:("__riscv_save_10", " __riscv_restore_10"),
                     3:("__riscv_save_12", " __riscv_restore_12") }
        # sanity = []
        for save in m_save_routines:
            if (save["Opt"] == []) : continue
            required_set = set([x["Source"][0] for x in save["Opt"]])
            (current_set,Found,Wasted_stores) = utils.Searchset(required_set,alist)
            if (Found):
                self.dprint("MSR Emulation wasted",Wasted_stores, len(Wasted_stores),colour="yellow",level=2)
                msr_address = self.retrieve_function_address(rfunction[alist.index(current_set)][0])
                sequence = utils.generate_jump_instructions(msr_address , int(save["Opt"][0]["PC"],16),"t0")
                save["JUMPSEQ"]= sequence

        for restore in m_restore_routines:
            if (restore["Opt"] == []) : continue
            required_set = set([x["Destination"][0] for x in restore["Opt"]])
            (current_set,Found,Wasted_loads) = utils.Searchset(required_set,alist)
            self.dprint("MSR Emulation wasted",Wasted_loads, len(Wasted_loads),colour="yellow",level=2)
            if (Found):
                msr_address = self.retrieve_function_address(rfunction[alist.index(current_set)][0])
                sequence = utils.generate_jump_instructions(msr_address , int(restore["Opt"][0]["PC"],16))
                restore["JUMPSEQ"]= sequence
            
        return (m_save_routines,m_restore_routines)




    def find_push_pop (self,both_encodings=False):
        stack_adj_push = list()
        stack_adj_pop = list()
        opt_empty = lambda opt: (len(opt["Adj"]) == 0 and len(opt["Opt"]) == 0 and opt["rcount_val"] == 0 )
        inst_match = lambda inst, target_inst : (("c." in inst and inst[2:] == target_inst) or inst == target_inst)
        # Make sure we are not running pushpop analysis on MSR files as it requires non MSR files ! TODO create fake MSR ! 
        assert not("__riscv_save_0" in [x.split("/")[1] for x in self.func]), self.filepath+" is compiled with MSR"
        # Variables depending if compressed version is used or if normal version is used
        store_inst = "sw" if (self.xlen == 32) else "sd"
        load_inst = "lw" if (self.xlen == 32) else "ld"
        maxstackadj = {"c.push":5*16,"c.popret":5*16,"c.pop":1*16,"push":31*16,"pop":31*16,"popret":31*16}


        stack_adj_push,stack_adj_pop = self.find_epilogue_prologue_lw_sw()

        # NOTE this is very reptitive dict of sets for all options, its written like this so we dont construct them at runtime hurting eval time  ! 
        rlist = {"c.push": [set(["ra"]),set(["ra", "s0"]),set(["ra", "s0","s1"]),set(["ra", "s0","s1","s2"]),
                        set(["ra", "s0","s1","s2","s3"]),set(["ra", "s0","s1","s2","s3","s4","s5"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11"])],
                "push": [set(["ra"]),set(["ra", "s0"]),set(["ra", "s0","s1"]),set(["ra","s0","s1","s2"]),
                        set(["ra", "s0","s1","s2","s3"]),set(["ra", "s0","s1","s2","s3","s4"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5"]),set(["ra", "s0","s1","s2","s3","s4","s5","s6"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8","s9"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10"]),
                        set(["ra", "s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11"])
                        ]
                }
        rlist["c.popret"] = rlist["c.push"]
        rlist["c.pop"] = rlist["c.push"]
        rlist["pop"] = rlist["push"]
        rlist["popret"] = rlist["push"]

        # List of embedded moves combinations for both compressed and 32 bit encodings !
        areg_list={  "ra":[],
                     "s0":("a0",),
                     "s1":("a0","a1"),
                     "s2":("a0","a1","a2"),
                     "s3":("a0","a1","a2","a3"),
                     "s4":("a0","a1","a2","a3"),  # NOTE Valid only in 32bit encoding ! 
                     "s5":("a0","a1","a2","a3"), 
                     "s6":("a0","a1","a2","a3"),  # NOTE Valid only in 32bit encoding ! 
                     "s7":("a0","a1","a2","a3"), 
                     "s8":("a0","a1","a2","a3"),  # NOTE Valid only in 32bit encoding ! 
                     "s9":("a0","a1","a2","a3"),  # NOTE Valid only in 32bit encoding ! 
                     "s10":("a0","a1","a2","a3"), # NOTE Valid only in 32bit encoding ! 
                     "s11":("a0","a1","a2","a3")}             
       # List of possible ret_value combinations for 
        ret_value = {"c.popret":("0",),"c.pop":(),"pop":("-1","1","0"),"popret":("-1","1","0")}
        #  Fitting stage (Make sure what we replace matches the encoding)
        
        Unmatch = 0
        for adj in stack_adj_push:   
            # Find the required register space and additional space aligned to 16 bytes
            required_set = set([x["Source"][0] for x in adj["Opt"]])
            register_space = int(self.xlen/8)*len(required_set)
            additional_space = ceil((abs(int(adj["Adj"]["Immediate"])) - register_space)/16)*16
            # NOTE This benchmarking code wont measure the performance mode of normal push instructions (which waste less store and load instructions !)
            inst = "push"
            Found = False
            # Check if compressed stack adjustment is enough !
            if  additional_space <= maxstackadj["c.push"]:
                inst = "c."+inst
            # if not, if we have enabled normal push and required stack adj is less than max, then we use push
            # Otherwise try to introduce ADDI16SP
            elif not(both_encodings and additional_space <= maxstackadj["push"]):
                inst = "c.push" if ((additional_space - maxstackadj["c.push"] < 512) or not both_encodings) else "push"
                additional_stack_adj = additional_space - maxstackadj[inst]
                # If we are out of range for stack adjustment, then check by how much and introduce ADDI16SP
                if (additional_stack_adj < 512):
                    adj["ADDI16SP"] = {"Immediate":-additional_stack_adj,"WoE":16}
                    self.dprint("Needed ADDI16SP at around",adj["Adj"]["PC"],"for ",additional_stack_adj,colour="red" )
                else:
                    inst = "c.push"
                    additional_stack_adj = additional_space - maxstackadj[inst]
                    if (additional_stack_adj < 2**11):
                        adj["ADDI16SP"] = {"Immediate":-additional_stack_adj,"WoE":32,"Instruction":"li"}
                        self.dprint("Needed ADDI16SP at around",adj["Adj"]["PC"],"for ",additional_stack_adj,colour="red" )
                    else:
                        self.dprint("Additional  ADDI16SP Out of range for",inst," at around",adj["Adj"]["PC"],"needed more",additional_stack_adj,colour="red" )
                        continue

            # Search the instruction to find the best correcsponding set ! 
            (current_set,Found,Wasted_stores) = utils.Searchset(required_set,rlist[inst])
            assert(Found)
            adj["Instruction"] = inst
            adj['WoE'] = 16 if ("c." in inst) else 32
            adj["rcount_val"] = current_set
            # Check embedded moves and see wastage !  NOTE we dont need to check if there is any because there is no 
            # disable flag for them in compressed instructions ! and len(adj["Embedded_moves"]) > 1
            needed_embedded_moves = set([x["Source"][0] for x in adj["Embedded_moves"]])
            required_embedded_moves = set(areg_list[sorted(current_set,key = lambda reg : utils.ABI_Reg_Names.index(reg))[-1]])
            
            # Modify structure to remove moves that wont fit so we dont remove them ! 
            adj["Embedded_moves"] = [x for x in adj["Embedded_moves"] if x["Source"][0] in required_embedded_moves]
            # RAW information for tuning encoding
            if(self.verbosity > 1):
                Found_statements = utils.roll_regs([x["Source"][0] for x in adj["Opt"]])
                self.dprint("Found",inst,Found_statements,":and fitted:",current_set,":for stack adj",adj["Adj"]["Immediate"], "and wasted",Wasted_stores, 
                            "needed ",utils.number_of_required_bits(int(additional_space/16),"unsigned"))
                wasted_embedded_moves = len(required_embedded_moves-needed_embedded_moves)
                self.dprint("Found embedded moves for",inst,needed_embedded_moves,"Fitting to embedded moves",required_embedded_moves,"for sreg",current_set,
                            "Saved",len(required_embedded_moves)-wasted_embedded_moves,"Wasted",wasted_embedded_moves)
            # End of RAW information for tuning encoding

        for adj in stack_adj_pop:
            # Get a list with all register names and find the required space for registers and any additional space 
            required_set = set([x['Destination'][0] for x in adj["Opt"]])
            register_space = int(self.xlen/8)*len(required_set)
            additional_space = ceil((abs(int(adj["Adj"]["Immediate"])) - register_space)/16)*16
            
            # Decide if we are matching to POP or POPRET
            inst = "popret" if (adj["Ret"]["Ret"] != None) else "pop"
            # For pop/ popret we need to have ra in the list, otherwise we cannot fit it since ra is allways popped !
            if "ra" not in required_set:
                continue
            elif additional_space <= maxstackadj[("c."+inst)]:
                inst = "c."+inst
            elif not (both_encodings and additional_space <= maxstackadj[inst]):
                inst = "c."+inst if ((additional_space - maxstackadj["c."+inst] < 496) or not both_encodings) else inst
                additional_stack_adj = additional_space - maxstackadj[inst]
                # If we are out of range for stack adjustment, then check by how much and introduce ADDI16SP
                if (additional_stack_adj < 496):
                    adj["ADDI16SP"] = {"Immediate":additional_stack_adj,"WoE":16}
                    self.dprint("Needed ADDI16SP at around",adj["Adj"]["PC"],"for ",additional_stack_adj,colour="red" )
                else:
                    if "c." not in inst: inst = "c." + inst
                    additional_stack_adj = additional_space - maxstackadj[inst]
                    if (additional_stack_adj < 2**11):
                        adj["ADDI16SP"] = {"Immediate":-additional_stack_adj,"WoE":32,"Instruction":"li"}
                        self.dprint("Needed ADDI16SP at around",adj["Adj"]["PC"],"for ",additional_stack_adj,colour="red" )
                    else:
                        self.dprint("Additional  ADDI16SP Out of range for",inst," at around",adj["Adj"]["PC"],"needed more",additional_stack_adj,colour="red" )
                        continue

            # Search the instruction to find the best correcsponding set that fits all required registers! 
            (current_set,Found,Waste) = utils.Searchset(required_set,rlist[inst])
            assert(Found)
        
            adj["Instruction"] = inst
            adj['WoE'] = 16 if ("c." in inst) else 32
            adj["rcount_val"] = current_set

            if ((adj["Ret"]["Ret"] != None and adj["Ret"]["Return_value"] != None ) and not(adj["Ret"]["Return_value"]["Immediate"] in ret_value[inst])):
                self.dprint("Rejected ",adj["Ret"]["Return_value"]["Immediate"]," as a return value because its not allowed for", inst,colour="yellow")
                adj["Ret"]["Return_value"] = None
                
            # RAW information for tuning encoding
            if(self.verbosity > 1):
                Found_statements = utils.roll_regs([x['Destination'][0] for x in adj["Opt"]])
                self.dprint("Found",inst ,Found_statements,":and fitted:",current_set,":for stack adj",adj["Adj"]["Immediate"], "and wasted", Waste, "needed ",utils.number_of_required_bits(int(additional_space/16),"unsigned"))
            # End of RAW information for tuning encoding



        return (stack_adj_push,stack_adj_pop)
                    


    def find_mv_chains(self,inst):
        ''' Find multiple instructions from the same type to chain them ! '''

        lresult = []
        gresult = []
        total_saving = 0      

        MVAS_Variations = {"c_mva01s07": (utils.unroll_reg("a0-a1"),utils.unroll_reg("s0-s7")),
                            "c_mva23s07":(utils.unroll_reg("a2-a3"), utils.unroll_reg("s0-s7")),
                            "c_mva01s03":(utils.unroll_reg("a0-a1"),utils.unroll_reg("s0-s3")),
                            "c_mva23s03":(utils.unroll_reg("a2-a3"),utils.unroll_reg("s0-s3"))}

        for function in sorted(self.main_dictionary):
            for pc_decimal in sorted(self.main_dictionary[function]):
                if ("Instruction" in self.main_dictionary[function][pc_decimal] and self.main_dictionary[function][pc_decimal]["Instruction"] == "c.mv"):
                    if ("HOB" in self.main_dictionary[function][pc_decimal]):
                        if (len(lresult)>0):
                            self.dprint("Discard double move buffer because of HOB",colour="yellow")
                        lresult.clear()
                    if ((self.main_dictionary[function][pc_decimal]["Source"][0]  in MVAS_Variations[inst][1] 
                        and self.main_dictionary[function][pc_decimal]['Destination'][0] in MVAS_Variations[inst][0])):
                        lresult.append(self.main_dictionary[function][pc_decimal])
                else:
                    if (len(lresult) > 1):
                        total_saving += ((sum([x['WoE'] for x in lresult])-16)/8)
                        gresult.append(list(lresult))
                        assert(len(lresult)==2)
                    lresult.clear()

        if (self.verbosity > 2):
            for result in gresult: 
                print(result)

        return (total_saving,gresult)

    def apply_optimization(self,old_instructions, optimization,mode=0):
        '''Mode 0 is used for instructions returned by find a chain 
           Mode 1 is used for a single list of instruction, where they will all be removed and the last one be updated 
           Mode 2 is used for a single instruction modifications where it replaces fields given in passed optimization
           Mode 4 is used for a single list of instruction, where they will all be removed and the first one be updated '''
        if (len(old_instructions) ==0):
            return
        elif (mode == 0):
            for chain in old_instructions:
                function_name = self.retrieve_function_limit(int(chain[0]['PC'],16),1)
                if (function_name == None):
                    continue
                for i,instruction in enumerate(chain):                            
                    if (i < len(chain)-1):
                        if (int(instruction['PC'],16) in self.main_dictionary[function_name]):
                            instruction_tbr = self.main_dictionary[function_name].pop(int(instruction['PC'],16))
                        else:
                            print("We are trying to remove an instruction twice at ",instruction['PC'], "?")
                            break
                        assert AssertionError(instruction_tbr['PC'] == instruction['PC'])
                    else:
                        self.main_dictionary[function_name][int(instruction['PC'],16)].update(optimization)
        elif (mode == 1 or mode == 4):
            old_instructions_itr = reversed(old_instructions) if (mode==4) else old_instructions
            function_name = self.retrieve_function_limit(int(old_instructions[0]['PC'],16),1)
            for i,instruction in enumerate(old_instructions_itr):
                if (function_name == None):
                    continue
                if (i < len(old_instructions)-1):
                    instruction_tbr = self.main_dictionary[function_name].pop(int(instruction['PC'],16))
                    assert AssertionError(instruction_tbr['PC'] == instruction['PC'])
                else:
                    self.main_dictionary[function_name][int(instruction['PC'],16)].update(optimization)
        elif (mode == 2):
            for instruction in old_instructions:
                function_name = self.retrieve_function_limit(int(instruction['PC'],16),1)
                if (function_name == None):
                    continue  
                self.main_dictionary[function_name][int(instruction['PC'],16)].update(optimization)



