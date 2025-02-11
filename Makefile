.PHONY: server client clean

server:
	python -m server --config config.json
client:
	python -m client --config config.json
clean:
	rm -rfv logs