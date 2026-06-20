%% File: ascelike.cls
%%
%% Version 3.0, March 2025
%%
%% An unofficial LaTeX class file for preparing review manuscripts and
%% camera-ready manuscripts for ASCE journals and conference proceedings
%%
%% =============================================
%% IMPORTANT NOTICE:
%% See the copyright and distribution conditions below.
%%
%% Copyright 2011:
%%  Matthew R Kuhn
%%  Donald P. Shiley School of Engineering
%%  University of Portland
%%  5000 N Willamette Blvd
%%  Portland OR  97203
%%  USA
%%  E-mail: kuhn@up.edu
%%
%% This program can be redistributed and/or modified under the terms
%% of the LaTeX Project Public License Distributed, available from the CTAN
%% archives; either version 1.1 of the License, or any later version.  
%% Most importantly, you may modify this file, but only if you rename it.
%%
%% This is a contributed file to the LaTeX2e system.
%%
%% This program consists of the files ascelike.cls and ascelike.bst
%%
%% -----------------------------------
%%
%% This document class produces manuscripts that roughly comply with
%% the guidelines of the American Society of Civil Engineers.  However,
%% it was not produced by ASCE, its agents, or employees; nor is it in
%% any way sanctioned or approved by that organization.
%%
%% -----------------------------------
%%
%% Please note the following usage:
%%
%%   1) This is a LATEX2E class file; it will not work with LaTeX 2.09.
%%
%%   2) It requires the following supplementary files:
%%        ifthen.sty    (part of the standard latex release)
%%        setspace.sty  (produces doubles spacing for journal manuscripts)
%%        endfloat.sty  (places figures and tables at the end of the manuscript)
%%        lineno.sty    (places line numbers alongside the text)
%%        authblk.sty   (collects the lists of authors and affiliations)
%%        biblatex.sty  processes citations and bibliographic entries
%%        babel.sty     required by biblatex
%%        newtxtext.sty approximations Times fonts
%%        newtxmath.sty approximations Times fonts
%%      Without these files, it won't work.  All of these files are included
%%      in modern distributions of LaTeX for Windows, Mac, and Linux sysgems.
%%      All of these files are also available from the CTAN archive, 
%%      currently at //http:www.tug.org/ctan.html
%%
%%   3) The following files can be used with the tool biber to produce 
%%      ASCE-like reference citations and entries (with the weird use of 
%%      quotation marks around titles, etc.)
%%        ascelike.bbx
%%        ascelike.cbx
%%        ascelike.bib  (an example bibliographic database for use with bibtex)
%%      Version 3.0 of asceline uses the "biblatex" and the "biber" helper
%%      program to process and format citations and bibliographic entries.
%%      Unfortunately, biblatex must be manually entered within the *.tex
%%      file, after the \documentclass line, as:
%%         \usepackage[backend=biber,uniquename=init,style=ascelike]{biblatex}
%%      Also, your bibliographic database is specified with the following
%%      command, for example:
%%         \addbibresource{ascexmpl.bib}
%%      Note the inclusion of the ".bib" suffix.  The following command places
%%      the reference section in your document:
%%         \printbibliography
%%      Finally, the biber helper program (not bibtex) to process the citations:
%%         biber <your tex file>.
%%
%%   3) There are several options.  The three main options are
%%         Journal, Proceedings, or Preprint:
%%         - "Journal" is the default format, and produces manuscripts intended
%%           for paper submissions to ASCE journals for review. The default
%%           settings of Journal are 12pt text, double-spaced text, numbered 
%%           lines, and in-text figures. These default settings can be altered 
%%           with the options that are described below.  The Journal option
%%           produces proper headings for sections, subsections, subsubsections,
%%           appendices, and the abstract, and it produces the proper page 
%%           margins and numbers the pages. Note that ASCE journals do not use
%%           numbered sections, subsections, or subsubsections.  This behavior
%%           can be changed with the \texttt{SectionNumbers} option.
%%         - "Proceedings" produces manuscripts for ASCE conference proceedings.
%%           As default settings, Proceedings uses single-spaced 12pt text,
%%           places figures and tables within the text, and does not number
%%           lines. All of these default settings can be altered with the 
%%           options that are described below. The Proceedings option produces
%%           proper headings for sections, subsections, subsubsections, 
%%           appendices, and the abstract.
%%         - "Preprint" produces an approximation of 2-column ASCE journal
%%           papers: single-space, 10pt, rules before and after the abstract,
%%           etc.  Using this options requires some manual adjustments of the
%%           *.tex file, as explained in the documentation, ascexmple.pdf
%%
%%       The remaining option override the defaults that are set by the
%%       above formats:
%%         - BackFigs or InsideFigs:
%%           These can be used to override the default placement of tables
%%           and figures for the Journal and Proceeding formats.
%%         - SingleSpace or DoubleSpace:
%%           These can be used to override the default text spacing for
%%           the Journal and Proceeding formats.
%%         - 10pt, 11pt, or 12pt:
%%           These can be used to override the default text size (12pt).
%%         - NoLists suppresses the inclusion of lists of figures and tables
%%         - NoPageNumbers suppressesthe printing of page numbers
%%         - SectionNumbers produces the numbering of sections and subsections,
%            unlike the ASCE convention.
%%
%% A few standard Latex options have been removed, as they don't seem to apply
%% in the ASCE environment: landscape, titlepage, openbib, leqno, fleqn
%%
%% As for preparing the document file: except for the new options, you
%% should just use standard sequencing of LaTeX commands.  
%%
%% The only new command that I've added is the \KeyWords command which 
%% prints your list of key words.
%%
%% Please contact Matthew Kuhn by email for suggestions, etc.
%%
\typeout{}
\NeedsTeXFormat{LaTeX2e}[1994/12/01]
\ProvidesClass{ascelike}
     [2025/03/17 Version 3.0 ASCE-like manuscripts (Am. Soc. Civ. Engr.)]
\typeout{}
\RequirePackage{ifthen}[1994/11/16]
\RequirePackage[american]{babel}
%\RequirePackage{csquotes}
%
\newboolean{Proceedings}
\newboolean{NewProceedings}  % accomodates legacy *.tex files
\newboolean{Preprint}
\newboolean{Journal}
\newboolean{BackFigs}
\newboolean{InsideFigs}
\newboolean{SingleSpace}
\newboolean{DoubleSpace}
\newboolean{NoPageNumbers}
\newboolean{NoLists}
\newboolean{SectionNumbers}
\newboolean{NoLineNumbers}
\newboolean{LineNumbers}
\newcommand{\ptsize}{}
%
\DeclareOption{Proceedings}%
              {\setboolean{Proceedings}{true}%
               \setboolean{Journal}{false}%
               \setboolean{Preprint}{false}}%
\DeclareOption{Journal}%
              {\setboolean{Journal}{true}%
               \setboolean{Proceedings}{false}%
               \setboolean{Preprint}{false}}%
\DeclareOption{Preprint}%
              {\setboolean{Preprint}{true}%
               \setboolean{Journal}{false}%
               \setboolean{Proceedings}{false}}%
\DeclareOption{NewProceedings}%
              {\setboolean{Proceedings}{true}%
               \setboolean{Journal}{false}%
               \setboolean{Preprint}{false}}%
%
\DeclareOption{BackFigs}%
              {\setboolean{BackFigs}{true}\setboolean{InsideFigs}{false}}
\DeclareOption{InsideFigs}%
              {\setboolean{InsideFigs}{true}\setboolean{BackFigs}{false}}
%
\DeclareOption{DoubleSpace}%
              {\setboolean{DoubleSpace}{true}\setboolean{SingleSpace}{false}}
\DeclareOption{SingleSpace}%
              {\setboolean{SingleSpace}{true}\setboolean{DoubleSpace}{false}}
%
\DeclareOption{NoLineNumbers}%
              {\setboolean{NoLineNumbers}{true}\setboolean{LineNumbers}{false}}
\DeclareOption{LineNumbers}%
              {\setboolean{LineNumbers}{true}\setboolean{NoLineNumbers}{false}}
%
% Declare text size options so that 12pt can be made the default option
\DeclareOption{10pt}{\renewcommand{\ptsize}{10pt}}
\DeclareOption{11pt}{\renewcommand{\ptsize}{11pt}}
\DeclareOption{12pt}{\renewcommand{\ptsize}{12pt}}
%
\DeclareOption{NoPageNumbers}{\setboolean{NoPageNumbers}{true}}
%
\DeclareOption{landscape}{\OptionNotUsed}
\DeclareOption{titlepage}{\OptionNotUsed}
\DeclareOption{openbib}{\OptionNotUsed}
\DeclareOption{leqno}{\OptionNotUsed}
\DeclareOption{fleqn}{\OptionNotUsed}
%
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
%
\DeclareOption{NoLists}{\setboolean{NoLists}{true}}
\DeclareOption{SectionNumbers}{\setboolean{SectionNumbers}{true}}
%
% Make 12pt and Journal the default options
\ExecuteOptions{12pt,Journal}
\ProcessOptions\relax
%
\LoadClass[oneside,onecolumn,letterpaper,final,\ptsize]{article}[1994/12/09]
%
% These *.sty packages must be installed along this *.cls file. Note that 
%   the package endfloat.sty is also required further below in order to
%   place figures at the end of the paper.
%
%
% Use these defaults
%   For Journal manuscripts:     
%            1) place figures within the text,
%               (can be changed with the BackFigs option)
%            2) double spacing of text
%               (can be changed with the SingleSpace option)
%            3) line numbers
%               (can be changed with the NoLineNumbers option)
%
%   For Proceedings manuscripts: 
%            1) place figures within the text,
%               (can be changed with the BackFigs option)
%            2) single spacing of text
%               (can be changed with the DoubleSpace option)
%            3) no line numbers
%               (can be changed with the LineNumbers option)
%
\ifthenelse{\boolean{Journal}}
  {\ifthenelse{\boolean{BackFigs}}{}{\setboolean{InsideFigs}{true}}}
  {\ifthenelse{\boolean{BackFigs}}{}{\setboolean{InsideFigs}{true}}}
%
\ifthenelse{\boolean{Journal}}
  {\ifthenelse{\boolean{SingleSpace}}{}{\setboolean{DoubleSpace}{true}}}
  {\ifthenelse{\boolean{DoubleSpace}}{}{\setboolean{SingleSpace}{true}}}
%
\ifthenelse{\boolean{Journal}}
  {\ifthenelse{\boolean{NoLineNumbers}}{}{\setboolean{LineNumbers}{true}}}
  {\ifthenelse{\boolean{LineNumbers}}{}{\setboolean{NoLineNumbers}{true}}}
%
\ifthenelse{\boolean{Preprint}}
  {\setboolean{LineNumbers}{false}
   \setboolean{NoLineNumbers}{true}
   \setboolean{DoubleSpace}{false}
   \setboolean{SingleSpace}{true}
   \setboolean{InsideFigs}{true}
   \setboolean{BackFigs}{false}
%  \renewcommand{\ptsize}{10pt}
%  \ExecuteOptions{10pt}
  }
  {}
%
% Various messages displayed on the screen:
\typeout{}
\ifthenelse{\boolean{Journal}}
  {\typeout{(1) A "Journal" style manuscript will be produced}}
  {\ifthenelse{\boolean{Proceedings}}
    {\typeout{(1) A "Proceedings" manuscript will be produced}}
    {\ifthenelse{\boolean{Preprint}}
      {\typeout{(1) A "Preprint" manuscript will be produced}}
      {}}}
%
\ifthenelse{\boolean{BackFigs}}
{\typeout{%
  (2) Figures and Tables will be placed together at the end of the manuscript
  (change with the 'InsideFigs' option)}}
{\typeout{%
  (2) Figures and Tables will be placed within the text of the manuscript
  (change with the 'BackFigs' option)}}
%
\ifthenelse{\boolean{DoubleSpace}}
{\typeout{%
  (3) Text will be double spaced (change with the 'SingleSpace' option)}}
{\typeout{%
  (3) Text will be single spaced (change with the 'DoubleSpace' option)}}
%
\typeout{(4) Text will be \ptsize 
 \space(change with the '10pt', '11pt', & '12pt' options)}
%
\ifthenelse{\boolean{LineNumbers}}%
{\typeout{%
  (5) Line numbers will be placed alonside the text (change with the
  'NoLineNumbers' option)}}
{\typeout{%
  (5) Line numbers will not be placed alonside the text (change with the
  'LineNumbers' option)}}
\typeout{}
%
% Delay the possible loading of these packages until the beginning of
% the document.  This should avoid conflicts with user-load versions
% of the same packages.
\AtBeginDocument{%
  \ifthenelse{\boolean{BackFigs}}
    {\ifthenelse{\boolean{NoLists}}%
      {\RequirePackage[nolists,noheads,nomarkers,tablesfirst]{endfloat}}%
      {\RequirePackage[lists,noheads,nomarkers,tablesfirst]{endfloat}}
  }
  {}
%
  \ifthenelse{\boolean{Preprint}}
    {\RequirePackage{multicol} \setlength{\columnsep}{8mm}
     \RequirePackage{float}}{}
%
  \ifthenelse{\boolean{DoubleSpace}}
%   {\RequirePackage{setspace}\begin{spacing}{1.5}}{}
    {\RequirePackage{setspace}\onehalfspacing}{}
%
  \ifthenelse{\boolean{LineNumbers}}
    {\RequirePackage{lineno}\linenumbers%
     \setlength{\linenumbersep}{0.3in}%
     \linenumberdisplaymath
    }{}
}%
%
\AtEndDocument{%
  \ifthenelse{\boolean{DoubleSpace}}
% {\end{spacing}}{}
  {}{}
}
%
% Page layout for Proceedings manuscripts:
\ifthenelse{\boolean{Proceedings}}
  {\setlength{\topmargin}     {0.00in}
   \setlength{\headheight}    {0.00in}
   \setlength{\headsep}       {0.00in}
   \setlength{\textheight}    {9.00in}
   \setlength{\footskip}      {0.50in}
   \setlength{\oddsidemargin} {0.00in}
   \setlength{\textwidth}     {6.50in}
   \setlength{\marginparsep}  {0.00in}
   \setlength{\marginparwidth}{0.00in}
   \setlength{\marginparpush} {0.00in}}
%
  {\ifthenelse{\boolean{Journal}}
%  Page layout for Journal manuscripts:
   {\setlength{\topmargin}     {0.00in}
    \setlength{\headheight}    {0.00in}
    \setlength{\headsep}       {0.00in}
    \setlength{\textheight}    {9.00in}
    \setlength{\footskip}      {0.50in}
    \setlength{\oddsidemargin} {0.00in}
    \setlength{\textwidth}     {6.50in}
    \setlength{\marginparsep}  {0.00in}
    \setlength{\marginparwidth}{0.00in}
    \setlength{\marginparpush} {0.00in}}
%
%  Page layout for Preprint manuscripts:
   {\ifthenelse{\boolean{Preprint}}
    {\setlength{\topmargin}     {-13mm}
     \setlength{\headheight}    {0.00in}
     \setlength{\headsep}       {0.00in}
     \setlength{\textheight}    {247mm}
     \setlength{\footskip}      {0.50in}
     \setlength{\oddsidemargin} {-10.4mm}
     \setlength{\textwidth}     {186mm}
     \setlength{\marginparsep}  {0.00in}
     \setlength{\marginparwidth}{0.00in}
     \setlength{\marginparpush} {0.00in}}
%
%   remainder layout
    {\setlength{\topmargin}     {0.00in}
     \setlength{\headheight}    {0.00in}
     \setlength{\headsep}       {0.00in}
     \setlength{\textheight}    {9.00in}
     \setlength{\footskip}      {0.50in}
     \setlength{\oddsidemargin} {0.00in}
     \setlength{\textwidth}     {6.50in}
     \setlength{\marginparsep}  {0.00in}
     \setlength{\marginparwidth}{0.00in}
     \setlength{\marginparpush} {0.00in}}}}
%
% use a font similar to Times New Roman
\RequirePackage{newtxtext}%
\RequirePackage{newtxmath}%
\RequirePackage[final,nopatch=footnote]{microtype}%
%
% packages for formatting author and affiliation in title
\RequirePackage{authblk}
\setcounter{Maxaffil}{10}
%
% An ASCE-like title on the first page.  ASCE wants a block format
% for the authors' affiliations. We use the package authblk.sty
% to collect the authors and affiliations.  These are collected in
% \AB@authlist and \AB@affillist.  The length \affilsep in authblk.sty
% does not do anything in ascelike.cls
  \ifthenelse{\boolean{Proceedings}}
    {\renewcommand{\@maketitle}
                  {\newpage\null\vspace{-8mm}% remove extra space
                   \begin{center}%
                     \let \footnote \thanks
                     {\normalfont\bfseries\@title\\[6mm]}%
                     {\AB@authlist\\[4mm]}% defined in authblk.sty
                   \end{center}
                   \ifthenelse{\equal{\AB@affillist}{}}
                     {}
                     {\AB@affillist\\[-4mm]}  % defined in authblk.sty
                  }%
     \renewcommand{\Authfont}{\normalfont\normalsize}
     \renewcommand{\Affilfont}{\normalfont\normalsize}
     \renewcommand\Authsep{; }
     \renewcommand\Authand{ and }
     \renewcommand\Authands{; and }
    }
    {%
     \renewcommand{\@maketitle}
                  {\newpage\null\vspace{2mm}% extra space
                   \begin{center}%
                     \let \footnote \thanks
                     {\Large\bfseries\sffamily\@title\\[5mm]}%
                     {\AB@authlist\\[3mm]}  % defined in authblk.sty
                   \end{center}%
                   \ifthenelse{\equal{\AB@affillist}{}}
                     {}
                     {\AB@affillist\\}      % defined in authblk.sty
                  }
     \renewcommand{\Authfont}{\large\sffamily}
     \renewcommand{\Affilfont}{\normalfont\normalsize}
%    \setlength{\affilsep}{1em}
     \renewcommand\Authsep{; }
     \renewcommand\Authand{ and }
     \renewcommand\Authands{; and }
    }
%
% An ASCE-like abstract, with the "abstract" name
\renewcommand{\abstractname}{%
  \ifthenelse{\boolean{Proceedings}}%
             {ABSTRACT}%
             {Abstract}}%
%
% format the abstract
\renewenvironment{abstract}
  {\ifthenelse{\boolean{Proceedings}}%
     {\normalsize\bfseries\noindent%
      \rule{0em}{2.6em}\abstractname:
      \normalfont\normalsize}
     {\ifthenelse{\boolean{Preprint}}%
        {\noindent\rule{\textwidth}{1.5pt}\\[-2.5mm]
     }{} % add top horiz. line
      \normalsize\bfseries\sffamily\noindent%
      \rule{0em}{2em}\abstractname:%
      \normalfont\normalsize}%
  }
  {\ifthenelse{\boolean{Preprint}}%
     {\\[-6pt]\noindent\rule[0pt]{\textwidth}{0.9pt}
     }% add bottom horiz. line
     {}
   \normalsize
  }
%
%
% ASCE-like section, subsection, and subsubsection headings
\ifthenelse{\boolean{SectionNumbers}}%
           {\setcounter{secnumdepth}{2}}%
           {\setcounter{secnumdepth}{0}}%
%
% section headings
\ifthenelse{\boolean{Proceedings}}%
  {\renewcommand{\section}{\@startsection{section}{1}{0in}%
                             {2.0ex \@plus 1.5ex \@minus .5ex}%
                             {2.0ex \@plus 0.2ex \@minus 1.5ex}%
                             {\normalsize\bfseries\rmfamily\uppercase}}%
  }%
  {\renewcommand{\section}{\@startsection{section}{1}{0in}%
                             {5.0ex \@plus 1ex \@minus 1.0ex}%
                             {2.0ex \@plus 0.5ex \@minus 0.5ex}%
                             {\large\bfseries\sffamily}}%
  }%
%
% subsection headings
\ifthenelse{\boolean{Proceedings}}%
  {\renewcommand{\subsection}{\@startsection{subsection}{2}{0in}%
                             {1.5ex \@plus 1ex \@minus .5ex}%
                             {1.5ex \@plus .5ex \@minus 1ex}%
                             {\normalsize\bfseries}}%
  }%
  {\renewcommand{\subsection}{\@startsection{subsection}{2}{0in}%
                             {4.0ex \@plus 1ex \@minus 1.0ex}%
                             {1.0ex \@plus 1ex \@minus 0.5ex}%
                             {\sffamily\bfseries\slshape}}%
  }%
%
% subsubsection headings
\ifthenelse{\boolean{Proceedings}}%
  {\renewcommand{\subsubsection}{\@startsection{subsubsection}{3}{0in}%
                             {1.5ex \@plus 1ex \@minus .5ex}%
                             {1.5ex \@plus 1ex \@minus .5ex}%
                             {\normalfont\normalsize\itshape}}%
  }%
  {\renewcommand{\subsubsection}{\@startsection{subsubsection}{3}{0in}%
                             {2.0ex \@plus 1ex \@minus .5ex}%
                             {0.3ex \@plus 0.5ex \@minus 0ex}%
                             {\rmfamily\normalsize\bfseries}}%
  }%
%
% suppress paragraph indentation for the first paragraph after a new section
% of journal articles
\ifthenelse{\boolean{Proceedings}}%
           {\setlength{\parindent}{6mm}}%
           {\setlength{\parindent}{4mm}%
            \let\@afterindenttrue\@afterindentfalse}%
%
% ASCE-like appendix headings.  In order to get appendix heading such as
%   'Appendix II: Notation' you must insert the line '\appendix' in your
%   document *.tex file at the start of the appendices.
%
\renewcommand{\appendixname}
             {\ifthenelse{\boolean{Proceedings}}%
                         {APPENDIX}
                         {Appendix}}
%
\renewcommand{\appendix}{%
  \renewcommand{\section}{%
    \secdef\Appendix\sAppendix}%
  \setcounter{section}{0}%
  \renewcommand{\thesection}{\Roman{section}}%
}
\newcommand{\Appendix}[2][]{%
   \refstepcounter{section}%
   {%
    \flushleft\normalsize\bfseries
    \ifthenelse{\boolean{Proceedings}}%
      {\rmfamily}%
      {\sffamily}%
    \appendixname\ %
    \thesection. \uppercase{#1}\par}\nopagebreak}%
\newcommand{\sAppendix}[1]{%
   {\flushleft\normalsize\bfseries%
    \ifthenelse{\boolean{Proceedings}}%
      {\rmfamily}%
      {\sffamily}%
    \uppercase{#1}\par}\nopagebreak}%
%
%
% An ASCE-like "enumerate" environment for numbered lists
\newcounter{enumnoo}
\renewenvironment{enumerate}
{\begin{list}
             {\arabic{enumnoo}.}%
             {\usecounter{enumnoo}%
              \setlength{\itemindent}{0ex}%
              \setlength{\listparindent}{1.5em}%
              \ifthenelse{\boolean{Proceedings}}%
                         {\setlength{\labelwidth}{1.5ex}%
                          \setlength{\labelsep}{1em}%
                          \setlength{\leftmargin}{3.5em}}%
                         {\setlength{\labelwidth}{1.5ex}%
                          \setlength{\labelsep}{2ex}%
                          \setlength{\leftmargin}{3.5ex}}%
              \setlength{\rightmargin}{0em}%
              \setlength{\parsep}{0ex}%
              \setlength{\topsep}{0ex}%
              \setlength{\itemsep}{0ex}%
             }%
}
{\end{list}}%
%
%
% An ASCE-like "itemize" environment for 'bulleted' items
\renewenvironment{itemize}
{\begin{list}
             {\small\labelitemi}%
             {\setlength{\labelwidth}{1.5ex}%
              \setlength{\labelsep}{2ex}%
              \setlength{\itemindent}{0em}%
              \setlength{\listparindent}{3em}%
              \ifthenelse{\boolean{Proceedings}}%
                         {\setlength{\leftmargin}{3em}}%
                         {\setlength{\leftmargin}{3.5ex}}%
              \setlength{\rightmargin}{0em}%
              \setlength{\parsep}{0ex}%
              \setlength{\topsep}{0ex}%
              \setlength{\itemsep}{0ex}%
             }%
}
{\end{list}}%
%
%
% ASCE-like figure and table captions
\RequirePackage{caption}
\ifthenelse{\boolean{Proceedings}}
 {\captionsetup{style=base,figurename=Figure,
                labelfont={bf},
                labelsep=period}
    \captionsetup[table]{position=above,skip=1pt}
    \captionsetup[figure]{position=below}}
 {\ifthenelse{\boolean{Journal}}
  {\captionsetup{style=base,figurename=Fig.,
                 labelfont={bf,sf},
                 labelsep=period,strut=true}
    \captionsetup[table]{position=above,skip=1pt}
    \captionsetup[figure]{position=below}}
  {\ifthenelse{\boolean{Preprint}}
   {\DeclareCaptionFormat{myformat}{#1#2#3\vspace{-0.8em}\hrulefill}
    \captionsetup{style=base,figurename=Fig.,
                  labelfont={bf,sf},
                  labelsep=period,strut=true}
    \captionsetup[table]{position=above,skip=1pt}
    \captionsetup[figure]{position=below,format=myformat}
   }{}
  }
 }
%
%
% Float parameters suggested by G. Granger in TUGboat 15(2)
\setcounter{topnumber}{2}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
\setcounter{dbltopnumber}{2}
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.5}
\renewcommand{\textfraction}{0.1}
\renewcommand{\floatpagefraction}{0.8}
\renewcommand{\dbltopfraction}{0.9}
\renewcommand{\dblfloatpagefraction}{0.8}
%
%
% An ASCE-like layout of the bibliographic items
\renewcommand{\refname}{%
  \ifthenelse{\boolean{Proceedings}}
    {\rule[-2.5ex]{0ex}{1ex}REFERENCES}
    {References}}
\def\@biblabel#1{}
\setlength{\bibindent}{1.0em}
%
\renewenvironment{thebibliography}[1]
     {\par%
      \section*{\refname}%
%     \@mkboth{\refname}{\refname}}%
      \list{[\arabic{enumiv}]}%
           {\setlength{\labelwidth}{0em}
            \leftmargin\labelwidth
            \setlength{\labelsep}{0.in}
            \advance\leftmargin\labelsep
            \advance\leftmargin\bibindent
            \itemindent -\bibindent
            \listparindent \itemindent
            \setlength{\itemsep}{0ex}%
            \setlength{\topsep}{0ex}%
            \parsep \z@
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand{\theenumiv}{\arabic{enumiv}}}%
      \sloppy\clubpenalty4000\widowpenalty4000%
      \sfcode`\.=\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}
\renewcommand{\newblock}{}
%
% define the default options for biblatex
\PassOptionsToPackage{backend=biber,uniquename=init,style=ascelike}{biblatex}
%
% commond for "tagging" the author's name at bottom right corner of pages
\newcommand{\NameTag}[1]
  {\ifthenelse{\boolean{NoPageNumbers}}
    {\@latex@warning{Oops! Can not use NameTag with NoPageNumbers}}
    {\ifthenelse{\boolean{Preprint}}{}  % no NameTag with Preprint option
     {\newlength{\LeftFootSpace}
      \settowidth{\LeftFootSpace}{#1}
      \renewcommand{\@oddfoot}{\hspace{\LeftFootSpace}\hfill\thepage\hfill#1}}}
  }
%
% name and format of Keywords
\newcommand{\KeyWordName}
           {\ifthenelse{\boolean{Proceedings}}
                       {Keywords}
                       {Author keywords}}
\newcommand{\KeyWords}[1]
  {\par\noindent\rule{0em}{3.5ex}%
   \ifthenelse{\boolean{Proceedings}}%
     {\rmfamily}%
     {\sffamily}%
   \bfseries\KeyWordName: %
   \normalfont#1}
%
% in two-column mode, one-column figures and tables require "H" placement
\ifthenelse{\boolean{Preprint}}
 {\renewcommand{\fps@figure}{H}
  \renewcommand{\fps@table}{H}}{}
%
% ASCE asks for the lists of tables and figures to be double-spaced
\ifthenelse{\boolean{BackFigs}}
{\renewcommand\listoftables{%
    \section*{\listtablename
      \@mkboth{%
          \MakeUppercase\listtablename}{\MakeUppercase\listtablename}}%
      \ifthenelse{\boolean{DoubleSpace}}%
        {\doublespacing\@starttoc{lot}\singlespacing}%
        {\@starttoc{lot}}}
 \renewcommand\listoffigures{%
    \section*{\listfigurename
      \@mkboth{\MakeUppercase\listfigurename}%
              {\MakeUppercase\listfigurename}}%
      \ifthenelse{\boolean{DoubleSpace}}%
        {\doublespacing\@starttoc{lof}\singlespacing}%
        {\@starttoc{lof}}}
    }{}
%
% redefine the \cite command in biblatex, so that it behaves as parencite.
% Also, introduce new citation commands
\AtBeginDocument{
  \@ifpackageloaded{biblatex}
%
% when both biblatex and hyperref are used, hyperref will only make the year
% contain the link. This code will make both the author and year contain 
% the link
    {\@ifpackageloaded{hyperref}
      {\DeclareFieldFormat{citehyperref}{%
       \DeclareFieldAlias{bibhyperref}{noformat}% Avoid nested links
       \bibhyperref{#1}}

     \DeclareFieldFormat{textcitehyperref}{%
       \DeclareFieldAlias{bibhyperref}{noformat}% Avoid nested links
       \bibhyperref{%
         #1%
         \ifbool{cbx:parens}
           {\bibcloseparen\global\boolfalse{cbx:parens}}
           {}}}

     \savebibmacro{cite}
     \savebibmacro{textcite}

     \renewbibmacro*{cite}{%
       \printtext[citehyperref]{%
         \restorebibmacro{cite}%
         \usebibmacro{cite}}}

     \renewbibmacro*{textcite}{%
       \ifboolexpr{
         ( not test {\iffieldundef{prenote}} and
           test {\ifnumequal{\value{citecount}}{1}} )
         or
         ( not test {\iffieldundef{postnote}} and
           test {\ifnumequal{\value{citecount}}{\value{citetotal}}} )
       }
         {\DeclareFieldAlias{textcitehyperref}{noformat}}
         {}%
       \printtext[textcitehyperref]{%
         \restorebibmacro{textcite}%
         \usebibmacro{textcite}}}}% \@ifpackageloaded{hyperref} = TRUE
    {}
%
\ifthenelse{\boolean{Proceedings}}
  {\defbibheading{bibliography}[REFERENCES]{\section*{#1}}
   \defbibenvironment{bibliography}
    {\list
      {}
      {\setlength{\leftmargin}{0em}%
       \setlength{\itemindent}{0em}%
       \setlength{\itemsep}{0.5em}%
       \setlength{\parsep}{\bibparsep}%
      }%
    }%
    {\endlist}
    {\item}
  }%
  {\defbibenvironment{bibliography}
    {\list
      {}
      {\setlength{\leftmargin}{\bibhang}%
       \setlength{\itemindent}{-\leftmargin}%
       \setlength{\itemsep}{\bibitemsep}%
       \setlength{\parsep}{\bibparsep}%
      }%
    }%
    {\endlist}
    {\item}
  }%
%
    \renewcommand\cite[1]{\parencite{#1}}
    \newcommand\citeNP[1]{\cite{#1}}
    \newcommand\citeA[1]{\citeauthor{#1}}
    \newcommand\citeN[1]{\textcite{#1}}
    \renewcommand\citeyear[1]{\parencite*{#1}}
    \renewcommand\citeNP[1]{\cite{#1}}}% @ifpackageloaded{biblatex} = TRUE
   {\typeout{^^J%
     OOPS! You have not loaded biblatex with the usepackage command.
     This might ^^Jresult in errors. We will proceed but will assume
     that you are using ^^J"bibtex" with the ascelike.bst style,
     and are not using "biber".^^J}
%   the next 45 lines are for backward compatability when biblatex is not used,
%   using code from an earlier version of ascelike.cls
    \let\@internalcite\cite
    \newcommand{\citedata}%
      {\@ifnextchar [{\@tempswatrue\@citedatax}%
                     {\@tempswafalse\@citedatax[]}}
%
    \def\@citedatax[#1]#2{%
    \if@filesw\immediate\write\@auxout{\string\citation{#2}}\fi%
      \def\@citea{}\@cite{\@for\@citeb:=#2\do%
        {\@citea\def\@citea{, }\@ifundefined% by Young
           {b@\@citeb}{{\bf ?}%
           \@warning{Citation `\@citeb' on page \thepage \space undefined}}%
    {\csname b@\@citeb\endcsname}}}{#1}}%
%
    \def\@citex[#1]#2{%
    \if@filesw\immediate\write\@auxout{\string\citation{#2}}\fi%
      \def\@citea{}\@cite{\@for\@citeb:=#2\do%
        {\@citea\def\@citea{; }\@ifundefined% by Young
           {b@\@citeb}{{\bf ?}%
           \@warning{Citation `\@citeb' on page \thepage \space undefined}}%
    {\csname b@\@citeb\endcsname}}}{#1}}%
    \renewcommand{\cite}%
       {\def\@citeseppen{-1000}%
        \def\@cite##1##2{(##1\if@tempswa , ##2\fi)}%
        \def\citeauthoryear##1##2##3{##2 ##3}\@internalcite}
    \newcommand{\citeNP}%
       {\def\@citeseppen{-1000}%
        \def\@cite##1##2{##1\if@tempswa , ##2\fi}%
        \def\citeauthoryear##1##2##3{##2 ##3}\@internalcite}
    \newcommand{\citeN}%
       {\def\@citeseppen{-1000}%
        \def\@cite##1##2{##1\if@tempswa , ##2)\else{)}\fi}%
        \def\citeauthoryear##1##2##3{##2 (##3}\citedata}
    \newcommand{\citeA}%
       {\def\@citeseppen{-1000}%
        \def\@cite##1##2{(##1\if@tempswa , ##2\fi)}%
        \def\citeauthoryear##1##2##3{##2}\@internalcite}
    \newcommand{\citeyear}%
       {\def\@citeseppen{-1000}%
        \def\@cite##1##2{(##1\if@tempswa , ##2\fi)}%
        \def\citeauthoryear##1##2##3{##3}\citedata}
    \newcommand{\citeyearNP}%
       {\def\@citeseppen{-1000}%
        \def\@cite##1##2{##1\if@tempswa , ##2\fi}%
        \def\citeauthoryear##1##2##3{##3}\citedata}%
%   \@ifpackageloaded{hyperref}
%   {}
   }
}
%
\AtEndOfClass
  {\bibliographystyle{ascelike}
   \ifthenelse{\boolean{NoPageNumbers}}
      {\pagestyle{empty}}
      {\pagestyle{plain}}
  }
%
