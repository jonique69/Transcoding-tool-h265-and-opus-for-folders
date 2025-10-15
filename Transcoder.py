#!/usr/bin/env python3
import os
import subprocess
import shutil
import platform
import re
from pathlib import Path
from tkinter import Tk, filedialog, messagebox

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Installare tqdm per la barra di progresso: pip install tqdm")

# Estensioni video supportate
VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg']

def select_folder_with_confirmation():
    """Apre un dialog per selezionare la cartella con conferma"""
    while True:
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder_path = filedialog.askdirectory(
            title='Seleziona la cartella con i video da convertire',
            initialdir=os.path.expanduser('~')
        )
        
        if not folder_path:
            root.destroy()
            return None
        
        # Conta i file video nella cartella
        video_count = len([
            f for f in Path(folder_path).iterdir() 
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
        ])
        
        # Chiedi conferma
        confirm_message = (
            f"Percorso selezionato:\n\n{folder_path}\n\n"
            f"File video trovati: {video_count}\n\n"
            f"Confermi di voler convertire i video in questa cartella?\n"
            f"(I file originali verranno sostituiti)"
        )
        
        confirmed = messagebox.askokcancel(
            "Conferma percorso",
            confirm_message,
            icon='warning'
        )
        
        root.destroy()
        
        if confirmed:
            return folder_path
        else:
            # Se l'utente cancella, chiedi se vuole riselezionare o uscire
            root2 = Tk()
            root2.withdraw()
            root2.attributes('-topmost', True)
            
            retry = messagebox.askyesno(
                "Riprova?",
                "Vuoi selezionare una cartella diversa?",
                icon='question'
            )
            
            root2.destroy()
            
            if not retry:
                return None

def get_available_encoders():
    """Rileva quali encoder hardware sono disponibili"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-encoders'],
            capture_output=True,
            text=True,
            check=True
        )
        
        encoders = result.stdout
        
        available = {
            'hevc_nvenc': 'hevc_nvenc' in encoders,
            'hevc_qsv': 'hevc_qsv' in encoders,
            'hevc_amf': 'hevc_amf' in encoders,
            'hevc_videotoolbox': 'hevc_videotoolbox' in encoders,
            'libx265': 'libx265' in encoders
        }
        
        return available
        
    except Exception as e:
        print(f"Errore rilevamento encoder: {e}")
        return {'libx265': True}

def detect_hardware_encoder():
    """Determina il miglior encoder hardware disponibile"""
    available = get_available_encoders()
    
    if available.get('hevc_videotoolbox'):
        return 'hevc_videotoolbox', 'Apple VideoToolbox'
    elif available.get('hevc_nvenc'):
        return 'hevc_nvenc', 'NVIDIA NVENC'
    elif available.get('hevc_qsv'):
        return 'hevc_qsv', 'Intel Quick Sync'
    elif available.get('hevc_amf'):
        return 'hevc_amf', 'AMD AMF'
    else:
        return 'libx265', 'Software (CPU)'

def get_encoder_params(encoder):
    """Restituisce i parametri ottimali per ogni encoder"""
    
    if encoder == 'hevc_nvenc':
        return {
            'video': [
                '-c:v', 'hevc_nvenc',
                '-preset', 'p7',
                '-rc', 'vbr',
                '-cq', '22',
                '-b:v', '0',
                '-spatial_aq', '1',
                '-temporal_aq', '1',
            ],
            'audio': [
                '-c:a', 'aac',
                '-b:a', '128k',
            ]
        }
    
    elif encoder == 'hevc_qsv':
        return {
            'video': [
                '-c:v', 'hevc_qsv',
                '-preset', 'slow',
                '-global_quality', '22',
                '-look_ahead', '1',
            ],
            'audio': [
                '-c:a', 'aac',
                '-b:a', '128k',
            ]
        }
    
    elif encoder == 'hevc_amf':
        return {
            'video': [
                '-c:v', 'hevc_amf',
                '-quality', 'quality',
                '-rc', 'cqp',
                '-qp_i', '22',
                '-qp_p', '22',
            ],
            'audio': [
                '-c:a', 'aac',
                '-b:a', '128k',
            ]
        }
    
    elif encoder == 'hevc_videotoolbox':
        return {
            'video': [
                '-c:v', 'hevc_videotoolbox',
                '-q:v', '60',
                '-tag:v', 'hvc1',
            ],
            'audio': [
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ac', '2',
            ]
        }
    
    else:
        return {
            'video': [
                '-c:v', 'libx265',
                '-crf', '22',
                '-preset', 'slow',
            ],
            'audio': [
                '-c:a', 'libopus',
                '-b:a', '96k',
                '-vbr', 'on',
                '-compression_level', '10',
            ]
        }

def get_video_duration(input_file):
    """Ottiene la durata del video in secondi"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(input_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return None

def convert_video(input_file, temp_dir, encoder, encoder_name):
    """Converte un singolo file video usando l'encoder specificato"""
    
    temp_output = Path(temp_dir) / f"{input_file.stem}_temp.mkv"
    
    params = get_encoder_params(encoder)
    
    command = [
        'ffmpeg',
        '-i', str(input_file),
        *params['video'],
        *params['audio'],
        '-map', '0:v',
        '-map', '0:a',
        '-progress', 'pipe:1',
        '-y',
        str(temp_output)
    ]
    
    try:
        print(f"\n[CONV] Conversione: {input_file.name}")
        print(f"   Encoder: {encoder_name}")
        print(f"   Dimensione originale: {input_file.stat().st_size / (1024**3):.2f} GB")
        
        duration = get_video_duration(input_file)
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        pbar = None
        if HAS_TQDM and duration:
            pbar = tqdm(
                total=duration,
                desc="   Progresso",
                unit="s",
                unit_scale=False,
                bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]'
            )
        
        current_time = 0
        for line in process.stdout:
            if 'out_time_ms=' in line:
                try:
                    time_ms = int(line.split('=')[1])
                    current_time = time_ms / 1000000.0
                    if pbar and duration:
                        pbar.n = min(current_time, duration)
                        pbar.refresh()
                except:
                    pass
        
        process.wait()
        
        if pbar:
            pbar.n = pbar.total
            pbar.refresh()
            pbar.close()
        
        if process.returncode != 0:
            stderr = process.stderr.read() if process.stderr else ""
            raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)
        
        if not temp_output.exists():
            raise Exception("File convertito non creato")
        
        original_size = input_file.stat().st_size / (1024**3)
        converted_size = temp_output.stat().st_size / (1024**3)
        compression = ((original_size - converted_size) / original_size) * 100
        
        print(f"   [OK] Conversione completata!")
        print(f"   Nuovo file: {converted_size:.2f} GB | Risparmio: {compression:.1f}%")
        print(f"   Sostituzione file originale...")
        
        input_file.unlink()
        final_path = input_file.parent / f"{input_file.stem}.mkv"
        shutil.move(str(temp_output), str(final_path))
        
        print(f"   [DONE] File sostituito: {final_path.name}")
        
        return True, original_size, converted_size
        
    except subprocess.CalledProcessError as e:
        print(f"   [ERROR] Errore durante la conversione")
        if hasattr(e, 'stderr') and e.stderr:
            error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
            print(f"   {error_msg[:200]}")
        
        if temp_output.exists():
            temp_output.unlink()
        
        return False, 0, 0
        
    except Exception as e:
        print(f"   [ERROR] Errore: {str(e)}")
        
        if temp_output.exists():
            temp_output.unlink()
        
        return False, 0, 0

def main():
    print("="*60)
    print("Convertitore Video H265 Multi-GPU")
    print("="*60)
    
    # Rileva encoder disponibile
    encoder, encoder_name = detect_hardware_encoder()
    print(f"\nEncoder rilevato: {encoder_name}")
    
    if encoder == 'libx265':
        print("ATTENZIONE: Nessun encoder hardware disponibile")
        print("Verrà usato encoding software (più lento)")
    
    # Seleziona la cartella con conferma
    print("\nSeleziona la cartella con i video...")
    input_dir = select_folder_with_confirmation()
    
    if not input_dir:
        print("\n[ANNULLATO] Operazione annullata dall'utente.")
        return
    
    input_path = Path(input_dir)
    print(f"\nCartella confermata: {input_path}")
    
    # Trova tutti i file video
    video_files = [
        f for f in input_path.iterdir() 
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]
    
    if not video_files:
        print(f"\n[ERROR] Nessun file video trovato")
        print(f"   Formati supportati: {', '.join(VIDEO_EXTENSIONS)}")
        return
    
    print(f"\nTrovati {len(video_files)} file video da convertire")
    print("\n" + "="*60)
    
    # Crea cartella temporanea nella stessa directory dei video
    temp_dir = input_path / ".video_conversion_temp"
    temp_dir.mkdir(exist_ok=True)
    
    print(f"Cartella temporanea creata in:")
    print(f"   {temp_dir}")
    print("   (Nella stessa cartella dei video - verrà eliminata al termine)\n")
    
    try:
        successful = 0
        failed = 0
        total_original_size = 0
        total_converted_size = 0
        
        # Converti ogni file
        for i, video_file in enumerate(video_files, 1):
            print(f"\n[{i}/{len(video_files)}]", end=" ")
            
            success, orig_size, conv_size = convert_video(
                video_file, temp_dir, encoder, encoder_name
            )
            
            if success:
                successful += 1
                total_original_size += orig_size
                total_converted_size += conv_size
            else:
                failed += 1
        
        # Riepilogo finale
        print("\n\n" + "="*60)
        print("CONVERSIONE COMPLETATA!")
        print("="*60)
        print(f"Successi: {successful}")
        print(f"Falliti: {failed}")
        
        if successful > 0:
            total_compression = ((total_original_size - total_converted_size) / total_original_size) * 100
            space_saved = total_original_size - total_converted_size
            
            print(f"\nSTATISTICHE TOTALI:")
            print(f"   Encoder usato: {encoder_name}")
            print(f"   Spazio originale: {total_original_size:.2f} GB")
            print(f"   Spazio finale: {total_converted_size:.2f} GB")
            print(f"   Spazio risparmiato: {space_saved:.2f} GB ({total_compression:.1f}%)")
    
    finally:
        # Rimuovi la cartella temporanea
        print(f"\nPulizia cartella temporanea...")
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                print(f"[OK] Cartella temporanea eliminata")
            except Exception as e:
                print(f"[WARN] Impossibile eliminare cartella temporanea: {e}")
                print(f"   Eliminala manualmente: {temp_dir}")
    
    print("\nProcesso terminato!\n")

if __name__ == "__main__":
    main()
