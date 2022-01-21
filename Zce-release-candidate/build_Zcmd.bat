del Zcmd.pdf
del *.svg
asciidoctor-pdf -r asciidoctor-diagram -a mathematical-format=svg -a pdf-style=..\..\docs-templates\resources\themes\risc-v_spec-pdf.yml -a pdf-fontsdir=..\..\docs-templates\resources\fonts Zcmd.adoc -o Zcmd.pdf