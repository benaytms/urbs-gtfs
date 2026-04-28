#!/bin/bash
URL="https://dadosabertos.c3sl.ufpr.br/curitibaurbs/"

DATE=$(date +"%Y_%m_%d_")
FILES=("linhas" "pois" "pontosLinha" "shapeLinha" "tabelaLinha" "tabelaVeiculo" "trechosItinerarios")
FORMAT=".json.xz"
FORMAT_DCM=".json"

DEST="$HOME/Templates/urbs-gtfs/source/"

if (ping -c1 8.8.8.8 &>/dev/null ); then
	echo "Site is UP! Fetching data..."
	for current_file in "${FILES[@]}"; do
		filename="$DATE$current_file$FORMAT"
		if [[ -e "$DEST$filename" ]]; then
			echo "$DEST$filename already downloaded. Skipping..."
		else
            decompressed="$DATE$current_file$FORMAT_DCM"
			if [[ -e "$DEST$decompressed" ]]; then
				echo "File already downloaded and decompressed. Skipping..."
			else
				sleep 3
				wget -q --show-progress -P "$DEST" "$URL$filename"
			fi
		fi
	done
else
	echo "Site is DOWN."
	exit 1
fi

for current_file in "${FILES[@]}"; do
	filename="$DATE$current_file$FORMAT"
	if [[ -e "$DEST$filename" ]]; then
		xz --decompress "$DEST$filename"
		echo "$current_file Decompression done."
	else
		echo "File already decompressed. Skipping..."
	fi
done

echo -e "\nSource:\n$(ls $DEST)"
exit 0
