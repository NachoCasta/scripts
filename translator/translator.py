# a simple parser for python. use get_number() and get_word() to read
def parser():
    while 1:
        data = list(input().split(' '))
        for number in data:
            if len(number) > 0:
                yield(number)   

input_parser = parser()

def get_word():
    global input_parser
    return next(input_parser)

def get_number():
    data = get_word()
    try:
        return int(data)
    except ValueError:
        return float(data)

# numpy and scipy are available for use
import numpy
import scipy
from time import sleep


code = ''' >,<>>,>,<[->-               
                                  >+<><<]+->>[-<<+>>]            
                                <+-><><<<[-+->-<+-<+>]<          
                               [->+<]><>>>>>><>++->>+->>         
                              >>>+[>><>>>[-]<[-<>-+]<<>[-        
                             +-]-++-+-<         [-]<><<>[+       
                            ---+]<><<             <<+-<<<<>      
                           -+<><<<>                 <+-<<[->     
                          >>>>>>+                     >>>>>-+    
                         >+<<<><            <          <><<<<<   
                        <<<<]>[           ->>           >>><><>  
                       ><>>+>>          >>>>+            <<<<<>< 
                      <<<<+-<           <<<]>             [->>>>>
                                        >><>+                    
                                        >>>>-                    
                                        +><>>                    
                                        +<<<<                    
                                        <<+-<                    
         <<<><<<<        -+><]     >>-++-+>+-+[<-]      <[->>    
      <>++-<<<]>>>>      [-<<<     +--+<<<<+>><>>>      >>>]>    
     [-<<-+<<<<<+<>>     +->>>     >>>]>[-<<<<><<<      ><<+>    
    >>>>>>]>>>>>><>>+    [-<<<     <+--+<><+-<<<<<      <[->>    
   +>>+<<<<]+->[->>+>>   +-+<<     <<]>[-<<+>>]>[-      <<+>>    
  ]+[[<>-]-++>[<-]<+-[   +--><     >><>-<<<]>>-+->      >>+>[    
 <-]<+-[-       >+>[-    <-]<[          >>[-<           <-+->    
 ]-<<[->         ><-     >+->-          +-<<<           <]]<]    
 >>-<<<           <      <+>[>          <<-]<           [>+->    
[-+<<-                   >]<<[          <]]>-           +-]>>    
>>><>>                   >><>+          ]-<<<           >+-<<    
<>+>-                    ++[<-          ]<[-+           >>+[<    
<<>->                    -+]<<          [>>>+           [<-+<    
<->>]                    <<<[<          ]]]>-           ]>>>>    
[-]<<                    <<<<<          -+<><           <<<<<    
<[-]>                    >+>+[          <-]<[           ->>+<    
><<<]                    >+>[<          -]<[>           >[<<-    
>]<<[                    <]]>-          [+>>>           >>>><    
++-++                    +++++          ++<<<           <<<+>    
+-[<<>                   -]<[>          >[<<-           >]<<[    
<]]>-[                   ++>[<          -]<[-           >>-<<    
 <]>>->           >      +>>+>          -[<-]           <[<<[    
 ->>>+<<         ><<     ]+->>          >>>+>           +[<><    
 -]<><[->       >+<<<    ]<<-<          ]<<<<           +>[<-    
  ]<[>>[<<->]<<[<]]>-]   >>+++          +++++[   ->     +++++    
   +<]>[-<<<<+>>>>]>>>   >>+><          >-+[<-]<[>>     [<<->    
    ]<<[<]]>-[++>[<-]    <[->>          -<<<]>>-<<<     <<<<<    
     +>+[<-]<[->>+<<     <]>>>          >>>>>+>[<-      ]<[>>    
      [<<->]<<[<]]>      -]<<[           -]<<<<<+>      [<-]<    
         [>>[<<->        ]<<[<            ]]>-]<<       [.<]!  '''
         

from sys import stdin, stdout


def find_bracket(code, pos, bracket):
    cont = 0
    pair = '[' if bracket == ']' else ']'
    for a, i in zip(code[pos:], range(pos, len(code))):
        if a == bracket:
            cont = cont + 1
        if a == pair:
            if cont == 0:
                return i
            else:
                cont = cont - 1

    raise Exception("Could not find `{}``bracket\nPosition: {}"
                    .format(pair, pos))


def prepare_code(code):
    def map_left_bracket(b, p):
        return (b, find_bracket(code, p + 1, b))

    def map_right_bracket(b, p):
        offset = find_bracket(list(reversed(code[:p])), 0, ']')
        return (b, p - offset)

    def map_bracket(b, p):
        if b == '[':
            return map_left_bracket(b, p)
        else:
            return map_right_bracket(b, p)

    return [map_bracket(c, i) if c in ('[', ']') else c
            for c, i in zip(code, range(len(code)))]


def read(string):
    valid = ['>', '<', '+', '-', '.', ',', '[', ']']
    return prepare_code([c for c in string if c in valid])


def eval_step(code, data, code_pos, data_pos, out=stdout.write, f=None):
    c = code[code_pos]
    d = data[data_pos]
    step = 1

    if c == '>':
        data_pos = data_pos + 1
        if data_pos > len(data):
            data_pos = 0
    elif c == '<':
        if data_pos != 0:
            data_pos -= 1
    elif c == '+':
        if d == 255:
            data[data_pos] = 0
        else:
            data[data_pos] += 1
    elif c == '-':
        if d == 0:
            data[data_pos] = 255
        else:
            data[data_pos] -= 1
    elif c == '.':
        print(chr(d), end="")
    elif c == ',':
        data[data_pos] = ord(f.read(1))
    else:
        bracket, jmp = c
        if bracket == '[' and d == 0:
            step = 0
            code_pos = jmp
        elif bracket == ']' and d != 0:
            step = 0
            code_pos = jmp

    return (data, code_pos, data_pos, step)


def evaluate(code, data=[0 for i in range(9999)], c_pos=0, d_pos=0, f=None):
    i = 0
    while c_pos < len(code):
        (data, c_pos, d_pos, step) = eval_step(code, data, c_pos, d_pos, f=f)
        c_pos += step
        if i % 1 == 0 and i < 1000:
            print(data[:6])
        i += 1
    print()
    print(data[:20])


#T = get_number()


import io

program = read(code)
f = io.StringIO(">=<")
evaluate(program, f=f)