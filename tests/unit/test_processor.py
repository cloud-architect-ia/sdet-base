from sdet_base.core.processor import run

def test_run_prints_correct_message(capfd, tmp_path):
    # Prepara un CSV de ejemplo
    file = tmp_path / "ejemplo.csv"
    file.write_text("col1\n1\n")

    # Llama a la función
    run(str(file))

    # Captura la salida
    captured = capfd.readouterr()
    assert "Procesando" in captured.out
    assert str(file) in captured.out
