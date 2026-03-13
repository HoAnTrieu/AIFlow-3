<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="19008000">
	<Property Name="varPersistentID:{382DE2CA-B6B6-4321-A9BF-8D514F68510A}" Type="Ref">/My Computer/GX3OPC.lvlib/OPERATE</Property>
	<Property Name="varPersistentID:{3A8DB08A-4759-4BA7-9C57-EDF8F41A7787}" Type="Ref">/My Computer/GX3OPC.lvlib/STATUS</Property>
	<Property Name="varPersistentID:{73754492-C2CE-4443-A26F-6CD53EC02666}" Type="Ref">/My Computer/GX3OPC.lvlib/DECISION</Property>
	<Property Name="varPersistentID:{D496124E-CAF1-40F1-925B-B7AB803857D3}" Type="Ref">/My Computer/GX3OPC.lvlib/ERRO-CODE</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="CanhTay.ctl" Type="VI" URL="../CanhTay.ctl"/>
		<Item Name="GX3OPC.lvlib" Type="Library" URL="../GX3OPC.lvlib"/>
		<Item Name="POWER-button.ctl" Type="VI" URL="../POWER-button.ctl"/>
		<Item Name="PythonToLabview.vi" Type="VI" URL="../PythonToLabview.vi"/>
		<Item Name="Sel-basket.ctl" Type="VI" URL="../Sel-basket.ctl"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="PythonToLabview" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{6D94F47F-0A12-417F-A5AF-40324441ACB3}</Property>
				<Property Name="App_INI_GUID" Type="Str">{68C400F6-ACE5-4715-86EE-0C1446A8B00E}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{036FD562-F87E-45E4-8FA1-06E4043DFACD}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">PythonToLabview</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../builds/NI_AB_PROJECTNAME/PythonToLabview</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{A4BEE294-D6D4-45C1-BA3C-1F36ABF94990}</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">Application.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../builds/NI_AB_PROJECTNAME/PythonToLabview/Application.exe</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../builds/NI_AB_PROJECTNAME/PythonToLabview/data</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{D3D814E8-9244-4C68-BC34-1F10679C6168}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/PythonToLabview.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">2</Property>
				<Property Name="TgtF_fileDescription" Type="Str">PythonToLabview</Property>
				<Property Name="TgtF_internalName" Type="Str">PythonToLabview</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2026 </Property>
				<Property Name="TgtF_productName" Type="Str">PythonToLabview</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{454CCA47-D0B8-447B-A983-4BD139A5BBEB}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">Application.exe</Property>
				<Property Name="TgtF_versionIndependent" Type="Bool">true</Property>
			</Item>
		</Item>
	</Item>
</Project>
