import ctypes
import time

def manter_tela_ativa():
    """
    Impede que o computador bloqueie a tela alterando o estado de inatividade.
    """
    try:
        # Evita o modo de suspensão e desliga o bloqueio automático
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
        print("Tela ativa. Pressione Ctrl+C para encerrar.")
        
        while True:
            time.sleep(60)  # Mantém o programa rodando
    except KeyboardInterrupt:
        # Restaura o comportamento padrão
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        print("\nComportamento padrão restaurado. Programa encerrado.")

if __name__ == "__main__":
    manter_tela_ativa()
