.PHONY: server client clean

server:
	python -m server --config config-server.json
client:
	python -m client --config config-client.json
clean:
	rm -rfv logs