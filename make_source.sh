rm -rf dist
mkdir dist
cp -r config i18n models utils main.py parse_lyrics.py process_image.py README.md config_simple.yaml requirements.txt dist
mv dist/config_simple.yaml dist/config.yaml
msgfmt dist/i18n/en/LC_MESSAGES/messages.po -o dist/i18n/en/LC_MESSAGES/messages.mo
msgfmt dist/i18n/zh/LC_MESSAGES/messages.po -o dist/i18n/zh/LC_MESSAGES/messages.mo
tar -czf macOS.zip dist
