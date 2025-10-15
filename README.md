# Transcoding-tool-h265-and-opus-for-folders

Questo è uno **strumento per la transcodifica di intere cartelle di file video**, progettato per ottimizzare lo spazio di archiviazione convertendo i contenuti nel formato più efficiente **H.265 (HEVC)**.

## Caratteristiche Principali

* **Alta Efficienza**: Transcodifica i video nel codec **H.265 (HEVC)** per ottenere file di dimensioni significativamente ridotte.

* **Compatibilità Massima e Zero Configurazione (Cross-System/Multi-GPU) 🚀**:
    * Il programma garantisce la massima compatibilità su tutti i sistemi (**Windows, macOS, Linux**).
    * Rileva e sfrutta **automaticamente** il miglior encoder hardware disponibile (come **NVIDIA NVENC**, **Intel Quick Sync**, **AMD AMF**, o **Apple VideoToolbox**), garantendo la massima velocità **senza alcuna configurazione manuale** da parte dell'utente.
    * Se l'accelerazione hardware non è disponibile, ricade in modo trasparente sull'encoder software `libx265` (CPU).

* **Audio Ottimizzato**: Utilizza il codec audio **Opus** (per l'encoding software `libx265`) o **AAC** (per gli encoder hardware).

* **Processo Batch e Sostituzione Diretta**: Consente di processare tutti i file video supportati in una cartella. I video originali vengono **sostituiti** direttamente dalla loro versione compressa in formato `.mkv`, liberando immediatamente lo spazio su disco.

* **Riepilogo e Statistiche**: Fornisce una barra di progresso e statistiche finali sul risparmio di spazio totale ottenuto.

***

## Intenzioni Future

Il progetto è attualmente uno script locale (Python) ma la visione futura include:

* **Sviluppo Lato Server**: L'obiettivo è evolvere lo strumento in un servizio di transcodifica gestito lato server. Questo permetterebbe agli utenti di sottoporre e gestire grandi volumi di conversioni in modo centralizzato, asincrono e ancora più scalabile.