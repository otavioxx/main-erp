param(
    [Parameter(Mandatory = $true)][string]$Alvo,
    [Parameter(Mandatory = $true)][string]$Launcher,
    [Parameter(Mandatory = $true)][string]$Sistema,
    [Parameter(Mandatory = $true)][string]$Icone,
    [Parameter(Mandatory = $true)][string]$AppId,
    [string[]]$Destinos = @(
        [Environment]::GetFolderPath('Desktop'),
        [Environment]::GetFolderPath('Programs')
    )
)

$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

public static class MainErpShortcutIdentity
{
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    private struct PropertyKey
    {
        public Guid FormatId;
        public uint PropertyId;
    }

    [StructLayout(LayoutKind.Explicit, Size = 24)]
    private struct PropVariant
    {
        [FieldOffset(0)] public ushort Type;
        [FieldOffset(8)] public IntPtr Value;
    }

    [ComImport, Guid("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IPropertyStore
    {
        void GetCount(out uint count);
        void GetAt(uint index, out PropertyKey key);
        void GetValue(ref PropertyKey key, out PropVariant value);
        void SetValue(ref PropertyKey key, ref PropVariant value);
        void Commit();
    }

    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    private class ShellLink { }

    [DllImport("ole32.dll")]
    private static extern int PropVariantClear(ref PropVariant value);

    public static void SetAppId(string path, string appId)
    {
        object link = new ShellLink();
        try
        {
            IPersistFile file = (IPersistFile)link;
            file.Load(path, 2);
            IPropertyStore store = (IPropertyStore)link;
            PropertyKey key = new PropertyKey {
                FormatId = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"),
                PropertyId = 5
            };
            PropVariant value = new PropVariant {
                Type = 31,
                Value = Marshal.StringToCoTaskMemUni(appId)
            };
            try
            {
                store.SetValue(ref key, ref value);
                store.Commit();
                file.Save(path, true);
            }
            finally
            {
                PropVariantClear(ref value);
            }
        }
        finally
        {
            Marshal.FinalReleaseComObject(link);
        }
    }
}
'@

$ws = New-Object -ComObject WScript.Shell
foreach ($pasta in @($Destinos + $Sistema) | Select-Object -Unique) {
    $caminho = Join-Path $pasta 'MainERP.lnk'
    $lnk = $ws.CreateShortcut($caminho)
    $lnk.TargetPath = $Alvo
    $lnk.Arguments = '"' + $Launcher + '"'
    $lnk.WorkingDirectory = $Sistema
    $lnk.IconLocation = $Icone
    $lnk.Description = 'MainERP - Sistema de Gest' + [char]0xE3 + 'o Empresarial'
    $lnk.Save()
    [MainErpShortcutIdentity]::SetAppId($caminho, $AppId)
    Write-Output ('Atalho criado: ' + $caminho)
}
