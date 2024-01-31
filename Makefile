HEADER_SOURCE := Zc-specification/Zc.adoc
PDF_RESULT := Zc.pdf

all: build

build:

	@echo "Building asciidoc"
	asciidoctor-pdf \
    -a compress \
    --attribute=mathematical-format=svg \
    --attribute=pdf-fontsdir=docs-resources/fonts \
    --attribute=pdf-style=docs-resources/themes/riscv-pdf.yml \
    --failure-level=ERROR \
    --require=asciidoctor-bibtex \
    --require=asciidoctor-diagram \
    --require=asciidoctor-mathematical \
    --out-file=$(PDF_RESULT) \
    $(HEADER_SOURCE)

clean:
	rm $(PDF_RESULT)
