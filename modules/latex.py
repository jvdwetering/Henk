import sys
import os

try:
    from .base import Module
except:
    from base import Module

template = r"""\documentclass{{article}}

\usepackage[utf8]{{inputenc}}
\usepackage{{amsfonts}}
\usepackage{{amsmath}}
\usepackage{{physics}}

\newcommand{{\R}}{{\mathbb{{R}}}}
\newcommand{{\C}}{{\mathbb{{C}}}}
\newcommand{{\N}}{{\mathbb{{N}}}}

\begin{{document}}
\pagestyle{{empty}}

\begin{{align*}}
    {}
\end{{align*}}

\end{{document}}
"""

error_types = {
    "Undefined control sequence": 0,
    "Runaway argument": 1,
    "Emergency stop": 2
}

import subprocess
import time

def latex_to_png(s):
    if os.path.isfile("latex.log"): os.remove("latex.log")
    if os.path.isfile("latex.pdf"): os.remove("latex.pdf")
    if os.path.isfile("latex.aux"): os.remove("latex.aux")
    if os.path.isfile("latex.png"): os.remove("latex.png")
    
    text = template.format(s)
    f = open("latex.tex", "w")
    f.write(text)
    f.close()

    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "latex.tex"],
                       stdout=subprocess.PIPE, shell=False,
                       universal_newlines=True)
    if "Fatal error occurred" in r.stdout: return "errawr", 0
    #print(str(r))
    time.sleep(0.2)
    
    command = []
    if sys.platform == 'win32': command.append('magick')
    else: command.append('convert')
    command.extend("-density 300 latex.pdf -trim -quality 90 latex.png".split(" "))
    r = subprocess.run(command, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    #return r
    time.sleep(0.2)
    f = open("latex.png", "rb")
    return f, 1


class Latex(Module):
    def register_commands(self,bot):
        bot.add_slash_command("latex", self.generate_latex)

    def generate_latex(self, bot, msg):
        f, success = latex_to_png(msg.command)
        if not success: return f
        bot.telebot.sendPhoto(msg.chat_id,f)
        return

latex = Latex()
        
