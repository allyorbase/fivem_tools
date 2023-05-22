import os
import sys
import argparse
import urllib.request
import shutil
import re
import json

import rarfile
import zipfile
import tarfile

from pathlib import Path
import xml.etree.ElementTree as ET

def extract_files(archive_path: Path, base_dir: Path, extensions: List[str], rename: Optional[str]) -> str:
    ped_name = rename
    archive = None

    if archive_path.suffix == ".zip":
        archive = ZipFile(archive_path, 'r')
    elif archive_path.suffix == ".tar":
        archive = tarfile.open(archive_path, 'r')
    elif archive_path.suffix == ".rar":
        archive = rarfile.RarFile(archive_path, 'r')
    else:
        print(f"Cannot extract files from an archive with extension '{archive_path.suffix}'")
        return None

    with archive:
        for file in archive.getnames() if isinstance(archive, (rarfile.RarFile, ZipFile)) else archive.getmembers():
            file_path = file.name if isinstance(file, tarfile.TarInfo) else file
            if file_path.endswith(tuple(extensions)):
                if ped_name is None:
                    ped_name = Path(file_path).stem
                # Extract the file to the base directory
                archive.extract(file, base_dir / ped_name)
                # Move the file to the top level of the created directory
                Path(base_dir / ped_name / file_path).rename(base_dir / ped_name / Path(file_path).name)

    return ped_name

def download_file(url, destination):
    print('Downloading file from {}'.format(url))
    urllib.request.urlretrieve(url, destination)

def add_ped_to_xml(ped_name, xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # find the InitDatas element
    init_datas = root.find('InitDatas')

    # load a template item
    item_template = ET.fromstring('''\
     <Item>
         <Name></Name>
         <ClipDictionaryName>move_m@generic</ClipDictionaryName>
         <ExpressionSetName>expr_set_ambient_male</ExpressionSetName>
         <Pedtype>CIVMALE</Pedtype>
         <MovementClipSet>move_m@business@c</MovementClipSet>
         <StrafeClipSet>move_ped_strafing</StrafeClipSet>
         <MovementToStrafeClipSet>move_ped_to_strafe</MovementToStrafeClipSet>
         <InjuredStrafeClipSet>move_strafe_injured</InjuredStrafeClipSet>
         <FullBodyDamageClipSet>dam_ko</FullBodyDamageClipSet>
         <AdditiveDamageClipSet>dam_ad</AdditiveDamageClipSet>
         <DefaultGestureClipSet>ANIM_GROUP_GESTURE_M_GENERIC</DefaultGestureClipSet>
         <FacialClipsetGroupName>facial_clipset_group_gen_male</FacialClipsetGroupName>
         <DefaultVisemeClipSet>ANIM_GROUP_VISEMES_M_LO</DefaultVisemeClipSet>
         <PoseMatcherName>Male</PoseMatcherName>
         <PoseMatcherProneName>Male_prone</PoseMatcherProneName>
         <GetupSetHash>NMBS_SLOW_GETUPS</GetupSetHash>
         <CreatureMetadataName>ambientPed_upperWrinkles</CreatureMetadataName>
         <DecisionMakerName>DEFAULT</DecisionMakerName>
         <MotionTaskDataSetName>STANDARD_PED</MotionTaskDataSetName>
         <DefaultTaskDataSetName>STANDARD_PED</DefaultTaskDataSetName>
         <PedCapsuleName>STANDARD_MALE</PedCapsuleName>
         <RelationshipGroup>CIVMALE</RelationshipGroup>
         <NavCapabilitiesName>STANDARD_PED</NavCapabilitiesName>
         <PerceptionInfo>DEFAULT_PERCEPTION</PerceptionInfo>
         <DefaultBrawlingStyle>BS_AI</DefaultBrawlingStyle>
         <DefaultUnarmedWeapon>WEAPON_UNARMED</DefaultUnarmedWeapon>
         <Personality>SERVICEMALES</Personality>
         <CombatInfo>DEFAULT</CombatInfo>
         <VfxInfoName>VFXPEDINFO_HUMAN_GENERIC</VfxInfoName>
         <AmbientClipsForFlee>FLEE</AmbientClipsForFlee>
         <AbilityType>SAT_NONE</AbilityType>
         <ThermalBehaviour>TB_WARM</ThermalBehaviour>
         <SuperlodType>SLOD_HUMAN</SuperlodType>
         <ScenarioPopStreamingSlot>SCENARIO_POP_STREAMING_NORMAL</ScenarioPopStreamingSlot>
         <DefaultSpawningPreference>DSP_NORMAL</DefaultSpawningPreference>
         <IsStreamedGfx value="false" />
     </Item>
      ''')

    # set the name in the template
    item_template.find('Name').text = ped_name

    # append the new item to the InitDatas element
    init_datas.append(item_template)

    # write the changes back to the XML file
    tree.write(xml_path)

def add_ped_to_json_vMenu(ped_name:str):
   json_file_path = Path("~/server-data/resources/vMenu/config/addons.json").expanduser()
   with open(json_file_path, 'r') as json_file:
       data = json.load(json_file)
    if 'peds' in data:
        data['peds'].append(ped_name)
    else:
        data['peds'] = [ped_name]
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def print_summary(archive_path: Path, new_directory: Path, ped_name: str):
    print("\nSUMMARY\n-------")
    print(f"Archive Extracted: {archive_path}")
    print(f"New directory: {new_directory}")
    print(f'Conents of {new_directory}:\n---------------------')
    for file in os.listdir(new_directory):
        print(f'- {file}')
    print(f"Ped name: {ped_name}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Install new ped")
    parser.add_argument('--url', help="Download link for packaged ped")
    parser.add_argument('--rename', help='Change name of ped for install')
    parser.add_argument('--file', help="path to ped archive or directory")
    args = parser.parse_args()

    if not args.url or not args.file:
        print("Error: Expecting a url or a file path")
        return 1;

    if args.url:
        # download file and save to /tmp/name_of_file
        archive_path = Path('/tmp', archive_path.split('/')[-1])
        download_file(args.url, archive_path)
    else:
        archive_path = Path(args.file)

    base_dir = Path("~/server-data/resources/assets/stream").expanduser()
    ped_name = extract_files(archive_path, base_dir, ['.ydd', '.yft', '.ymt', '.ytd'], args.rename)

    if ped_name:
        # Add to the peds.meta xml
        update_xml(ped_name, Path("~/server-data/resources/assets/peds.meta").expanduser() )
        print(f"Ped model '{ped_name}' has been added to peds.meta")

        # Add to vMenu
        add_ped_to_json_vMenu(ped_name)
        print(f"Ped model '{ped_name}' has been added to vMenu")

        # Print summary
        print_summary(archive_path, base_dir, ped_name)

    else:
        print("No files were extracted. Please ensure the archive contains the right files.")
