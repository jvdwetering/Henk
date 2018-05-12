import sys
import os

try:
    from .base import Module
except:
    from base import Module

template1 = r"""\documentclass{{article}}

\usepackage[utf8]{{inputenc}}
\usepackage{{amsfonts}}
\usepackage{{amsmath}}
\usepackage{{amsthm}}
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

template2 = r"""\documentclass{{article}}

\usepackage[utf8]{{inputenc}}
\usepackage{{minted}}

\begin{{document}}
\pagestyle{{empty}}

\begin{{minted}}{{{}}}
    {}
\end{{minted}}

\end{{document}}
"""

error_types = {
    "Undefined control sequence": 0,
    "Runaway argument": 1,
    "Emergency stop": 2
}

import subprocess
import time

def latex_to_png(latex):
    if os.path.isfile("latex.log"): os.remove("latex.log")
    if os.path.isfile("latex.pdf"): os.remove("latex.pdf")
    if os.path.isfile("latex.aux"): os.remove("latex.aux")
    if os.path.isfile("latex.png"): os.remove("latex.png")
    
    f = open("latex.tex", "w")
    f.write(latex)
    f.close()

    r = subprocess.run(["pdflatex", "-shell-escape", "-interaction=nonstopmode", "latex.tex"],
                       stdout=subprocess.PIPE, shell=False,
                       universal_newlines=True)
    if "Fatal error occurred" in r.stdout:
        return r
        return "errawr", 0
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

def math_to_png(s):
    return latex_to_png(template1.format(s))

def code_to_png(s, language='python'):
    return latex_to_png(template2.format(language, s))


class Markup(Module):
    def register_commands(self,bot):
        bot.add_slash_command("latex", self.generate_latex)
        bot.add_slash_command("python", self.gen_lang_command("python"))
        bot.add_slash_command("c", self.gen_lang_command("c"))
        bot.add_slash_command("java", self.gen_lang_command("java"))
        bot.add_slash_command("php", self.gen_lang_command("php"))
        bot.add_slash_command("html", self.gen_lang_command("html"))

    def gen_lang_command(self, lang):
        def f(bot, msg):
            f, success = code_to_png(msg.command, lang)
            if not success: return f
            bot.telebot.sendPhoto(msg.chat_id,f)
            return
        return f

    def generate_latex(self, bot, msg):
        f, success = latex_to_png(msg.command)
        if not success: return f
        bot.telebot.sendPhoto(msg.chat_id,f)
        return

    def generate_python(self, bot, msg):
        f, success = code_to_png(msg.command)
        if not success: return f
        bot.telebot.sendPhoto(msg.chat_id,f)
        return

markup = Markup()
        
