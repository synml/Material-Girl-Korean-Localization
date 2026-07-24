//=============================================================================
// RTK1_Option_EnJa.js  ver1.13 2016/07/12
// The MIT License (MIT)
//=============================================================================

/*:
 * @plugindesc Plugin to select English/Japanese language in Option menu.
 * @author Toshio Yamashita (yamachan)
 *
 * @param switch
 * @desc Switch number : ON is Japanese, OFF is English
 * (0:OFF 1-999:Switch No.)
 * @default 0
 *
 * @param hide
 * @desc Hide Language in Option screen (0:OFF 1:ON)
 * @default 0
 *
 * @param message
 * @desc Expand text message with dictionary (0:OFF 1:ON)
 * @default 0
 *
 * @param meta_ja
 * @desc Meta tag name for Japanese text in Note area
 * @default ja
 *
 * @param meta_en
 * @desc Meta tag name for English text in Note area
 * @default en
 *
 * @param separator
 * @desc Separator string for setName,Nickname,Profile
 * @default ||
 *
 * @param separator_note
 * @desc Separator string in Note tag
 * @default ,
 *
 * @param 2nd_language
 * @desc The name of 2nd language
 * @default Japanese
 *
 * @help
 * This plugin requires RTK1_Core plugin (1.12 or later) previously.
 *
 * Plugin Command:
 *   RTK1_Option_EnJa english    # Change to English mode
 *   RTK1_Option_EnJa japanese   # Change to Japanese mode
 *
 * https://github.com/yamachan/jgss-hack/blob/master/RTK1_Option_EnJa.md
 */

/*:ja
 * @plugindesc オプションメニューで言語を英語と日本語で切り替えるプラグイン
 * @author Toshio Yamashita (yamachan)
 *
 * @param switch
 * @desc Switch番号 : ONは日本語、OFFは英語
 * (0:OFF 1-999:Switch番号)
 * @default 0
 
 * @param variable
 * @desc variable番号 : 0：日本語
 * (0:OFF 1-999:Switch番号)
 * @default 0
 *
 * @param hide
 * @desc 言語切り替えをオプションメニューから隠します (0:OFF 1:ON)
 * @default 0
 *
 * @param message
 * @desc テキストメッセージを拡張します (0:OFF 1:ON)
 * @default 0
 *
 * @param meta_ja
 * @desc ノート欄で日本語テキストを指定するタグ名
 * @default ja
 *
 * @param meta_en
 * @desc ノート欄で英語テキストを指定するタグ名
 * @default en
 *
 * @param separator
 * @desc Name,Nickname,Profileを指定するときの区切り文字
 * @default ||
 *
 * @param separator_note
 * @desc ノート欄のタグ内のテキストデータで使用する区切り文字
 * @default ,
 *
 * @param 2nd_language
 * @desc 本プラグインで追加表示する言語の名称
 * @default Japanese
 *
 * @help
 * このプラグインの前に RTK1_Core プラグイン(1.12以降)を読み込んでください。
 *
 * プラグインコマンド:
 *   RTK1_Option_EnJa english    # 英語モードにする
 *   RTK1_Option_EnJa japanese   # 日本語モードにする
 *
 * https://github.com/yamachan/jgss-hack/blob/master/RTK1_Option_EnJa.ja.md
 */

//-----------------------------------------------------------------------------

(function(_global) {
	if (!_global["RTK"]) {
		throw new Error('This plugin requires RTK1_Core.js plugin previously.');
	}
	if (RTK.VERSION_NO < 1.13) {
		throw new Error('This plugin requires version 1.13 or later of RTK1_Core plugin. the current version looks ' + RTK.VERSION_NO + ".");
	}

	var N = "RTK1_Option_EnJa";
	var NK = "RTK_EJ";
	var M = RTK["EJ"] = RTK._modules[N] = {};

	var param = PluginManager.parameters(N);
	//M._switch = Number(param['switch'] || 0);
	M._variable = Number(param['variable'] || 0);
	M._hide = Number(param['hide'] || 0);
	M._message = Number(param['message'] || 0);
	M._meta_ja = param['meta_ja'] || "ja";
	M._meta_en = param['meta_en'] || "en";
	M._meta_chi = param['meta_ch'] || "ch";
	M._separator = param['separator'] || "||";
	M._separator_note = param['separator_note'] || ",";
	M._2nd_language = param['2nd_language'] || "English";
	M._3nd_language = param['3nd_language'] || "Chinese";

	// ----- Init resource -----

	var terms_E, actors_E, classes_E, items_E, weapons_E, armors_E, enemies_E, troops_E, skills_E, states_E;
	var terms_C, actors_C, classes_C, items_C, weapons_C, armors_C, enemies_C, troops_C, skills_C, states_C;
	var terms_J, actors_J, classes_J, items_J, weapons_J, armors_J, enemies_J, troops_J, skills_J, states_J;
	var t_weapons_E, t_armors_E, t_equips_E, t_skills_E, t_elements_E;
	var t_weapons_C, t_armors_C, t_equips_C, t_skills_C, t_elements_C;
	var t_weapons_J, t_armors_J, t_equips_J, t_skills_J, t_elements_J;

	RTK.onReady(function(){
		switch(RTK._lang){
			case 0:
				
				terms_E = $dataSystem.terms;
				actors_E = $dataActors;
				classes_E = $dataClasses;
				items_E = $dataItems;
				weapons_E = $dataWeapons;
				armors_E = $dataArmors;
				enemies_E = $dataEnemies;
				troops_E = $dataTroops;
				skills_E = $dataSkills;
				states_E = $dataStates;
				t_weapons_E = $dataSystem.weaponTypes;
				t_armors_E = $dataSystem.armorTypes;
				t_equips_E = $dataSystem.equipTypes;
				t_skills_E = $dataSystem.skillTypes;
				t_elements_E = $dataSystem.elements;

				terms_J = M._terms_J;
				actors_J = updateGameData(actors_E, M.translation.actors, M._meta_ja);
				classes_J = updateGameData(classes_E, M.translation.classes, M._meta_ja);
				items_J = updateGameData(items_E, M.translation.items, M._meta_ja);
				weapons_J = updateGameData(weapons_E, M.translation.weapons, M._meta_ja);
				armors_J = updateGameData(armors_E, M.translation.armors, M._meta_ja);
				enemies_J = updateGameData(enemies_E, M.translation.enemies, M._meta_ja);
				troops_J = updateGameData(troops_E, M.translation.troops, M._meta_ja);
				skills_J = updateGameData(skills_E, M.translation.skills, M._meta_ja);
				states_J = updateGameData(states_E, M.translation.states, M._meta_ja);
				t_weapons_J = updateTypeData(t_weapons_E, M.translation.t_weapons);
				t_armors_J = updateTypeData(t_armors_E, M.translation.t_armors);
				t_equips_J = updateTypeData(t_equips_E, M.translation.t_equips);
				t_skills_J = updateTypeData(t_skills_E, M.translation.t_skills);
				t_elements_J = updateTypeData(t_elements_E, M.translation.t_elements);
				
				terms_C = M._terms_C;
				actors_C = updateGameData(actors_J, M.translation.actors, M._meta_chi);
				classes_C = updateGameData(classes_J, M.translation.classes, M._meta_chi);
				items_C = updateGameData(items_J, M.translation.items, M._meta_chi);
				weapons_C = updateGameData(weapons_J, M.translation.weapons, M._meta_chi);
				armors_C = updateGameData(armors_J, M.translation.armors, M._meta_chi);
				enemies_C = updateGameData(enemies_J, M.translation.enemies, M._meta_chi);
				troops_C = updateGameData(troops_J, M.translation.troops, M._meta_chi);
				skills_C = updateGameData(skills_J, M.translation.skills, M._meta_chi);
				states_C = updateGameData(states_J, M.translation.states, M._meta_chi);
				t_weapons_C = updateTypeData(t_weapons_J, M.translation.t_weapons);
				t_armors_C = updateTypeData(t_armors_J, M.translation.t_armors);
				t_equips_C = updateTypeData(t_equips_J, M.translation.t_equips);
				t_skills_C = updateTypeData(t_skills_J, M.translation.t_skills);
				t_elements_C = updateTypeData(t_elements_J, M.translation.t_elements);
				
				break;
			case 1:
				
				terms_J = $dataSystem.terms;
				actors_J = $dataActors;
				classes_J = $dataClasses;
				items_J = $dataItems;
				weapons_J = $dataWeapons;
				armors_J = $dataArmors;
				enemies_J = $dataEnemies;
				troops_J = $dataTroops;
				skills_J = $dataSkills;
				states_J = $dataStates;
				t_weapons_J = $dataSystem.weaponTypes;
				t_armors_J = $dataSystem.armorTypes;
				t_equips_J = $dataSystem.equipTypes;
				t_skills_J = $dataSystem.skillTypes;
				t_elements_J = $dataSystem.elements;

				terms_E = M._terms_E;
				actors_E = updateGameData(actors_J, M.translation.actors, M._meta_en);
				classes_E = updateGameData(classes_J, M.translation.classes, M._meta_en);
				items_E = updateGameData(items_J, M.translation.items, M._meta_en);
				weapons_E = updateGameData(weapons_J, M.translation.weapons, M._meta_en);
				armors_E = updateGameData(armors_J, M.translation.armors, M._meta_en);
				enemies_E = updateGameData(enemies_J, M.translation.enemies, M._meta_en);
				troops_E = updateGameData(troops_J, M.translation.troops, M._meta_en);
				skills_E = updateGameData(skills_J, M.translation.skills, M._meta_en);
				states_E = updateGameData(states_J, M.translation.states, M._meta_en);
				t_weapons_E = updateTypeData(t_weapons_J, M.translation.t_weapons);
				t_armors_E = updateTypeData(t_armors_J, M.translation.t_armors);
				t_equips_E = updateTypeData(t_equips_J, M.translation.t_equips);
				t_skills_E = updateTypeData(t_skills_J, M.translation.t_skills);
				t_elements_E = updateTypeData(t_elements_J, M.translation.t_elements);
				
				terms_C = M._terms_C;
				actors_C = updateGameData(actors_J, M.translation.actors, M._meta_chi);
				classes_C = updateGameData(classes_J, M.translation.classes, M._meta_chi);
				items_C = updateGameData(items_J, M.translation.items, M._meta_chi);
				weapons_C = updateGameData(weapons_J, M.translation.weapons, M._meta_chi);
				armors_C = updateGameData(armors_J, M.translation.armors, M._meta_chi);
				enemies_C = updateGameData(enemies_J, M.translation.enemies, M._meta_chi);
				troops_C = updateGameData(troops_J, M.translation.troops, M._meta_chi);
				skills_C = updateGameData(skills_J, M.translation.skills, M._meta_chi);
				states_C = updateGameData(states_J, M.translation.states, M._meta_chi);
				t_weapons_C = updateTypeData(t_weapons_J, M.translation.t_weapons);
				t_armors_C = updateTypeData(t_armors_J, M.translation.t_armors);
				t_equips_C = updateTypeData(t_equips_J, M.translation.t_equips);
				t_skills_C = updateTypeData(t_skills_J, M.translation.t_skills);
				t_elements_C = updateTypeData(t_elements_J, M.translation.t_elements);
				
				break;
			
			case 2:
				break;
		}
		RTK.onCall(N, function(args){
			if (args.length == 1 && args[0].match(/^ja(?:panese)?$/i)) {
				RTK.terms_change(0);
				ConfigManager.save();
			} else if (args.length == 1 && args[0].match(/^en(?:glish)?$/i)) {
				RTK.terms_change(1);
				ConfigManager.save();
			} else if (args.length == 1 && args[0].match(/^chi(?:nese)?$/i)) {
				RTK.terms_change(2);
				ConfigManager.save();
			}
		});
		RTK.log(N + " ready (_lang:" + RTK._lang + "_variable:" + M._variable + ", _hide:" + M._hide + ", _message:" + M._message + ")");
	});

	function cloneObject(_s) {
		if (!_s) { return null; }
		if (_s.cloneFrom) { return _s; }
		var o = RTK.cloneObject(_s);
		o._cloneFrom = _s;
		return o;
	};
	function updateObject(_o, _v) {
		if (!_o) {return; }
		if ("string" == typeof _v ) {
			var a = _v.split(M._separator_note);
			if (a[0] != "") {
				_o.name = a[0];
			}
			if (a.length > 1 && a[1] != "") {
				if (_o.nickname !== undefined) {
					_o.nickname = a[1];
				} else if (_o.description !== undefined) {
					_o.description = a[1];
				} else {
					if (_o.note !== undefined) {
						_o.note = a[1];
					}
					return;
				}
			}
			if (a.length > 2 && a[2] != "") {
				if (_o.profile !== undefined) {
					_o.profile = a[2];
				} else {
					if (_o.note !== undefined) {
						_o.note = a[2];
					}
					return;
				}
			}
			if (a.length > 3 && a[3] != "") {
				if (_o.note !== undefined) {
					_o.note = a[3];
				}
			}
		} else {
		}
	};
	function updateGameData(_list, _data, _meta) {
		_list = _list.clone();

		// ----- Apply meta values -----
		for (var l=0; l<_list.length; l++) {
			if (_list[l] && _list[l].meta) {
				var s = _list[l].meta[_meta];
				if ("string" == typeof s && s != "") {
					_list[l] = cloneObject(_list[l]);
					updateObject(_list[l], s);
				}
			}
		}

		// ----- Apply translated values -----
		var id = 1;
		for (var l=0; l<_data.length; l++) {
			var d = _data[l];
			if ("string" == typeof d && d != "") {
				_list[id] = cloneObject(_list[id]);
				updateObject(_list[id], d);
			} else if ("object" == typeof d) {
				if (d.id) {
					id = d.id;
				}
				for (var k in d) {
					if (d.hasOwnProperty(k)) {
						_list[id][k] = d[k];
					}
				}
			}
			id++;
		}
		return _list;
	};
	function updateTypeData(_list, _data) {
		var ret = _list.clone();
		for (var l=0; l<_list.length; l++) {
			var a = _list[l].split(M._separator);
			if (a.length == 2) {
				_list[l] = a[0];
				ret[l] = a[1];
			}
		}
		for (var l=0; l<_data.length; l++) {
			var d = _data[l];
			if ("string" == typeof d && d != "") {
				ret[l] = d;
			}
		}
		return ret;
	};

	// ----- Enhance option menu -----
	
	ConfigManager.SymbolSpecialVal['langSelect'] = 2;

	Object.defineProperty(ConfigManager, 'langSelect', {
	    get: function() {
	        return M._langSelect;
	    },
	    set: function(_value) {
	        M._langSelect = _value;
	    },
	    configurable: true
	});
	var _ConfigManager_makeData = ConfigManager.makeData;
	ConfigManager.makeData = function() {
		var config = _ConfigManager_makeData.call(this);
		config.langSelect = this.langSelect;
		return config;
	};

	var _ConfigManager_applyData = ConfigManager.applyData;
	ConfigManager.applyData = function(config) {
		_ConfigManager_applyData.call(this, config);
		this.langSelect = this.readVolume2(config, 'langSelect');
	};
	
	ConfigManager.readVolume2 = function(config, name) {
		var value = config[name];
		if (value !== undefined) {
			return Number(value).clamp(1, 2);
		} else {
			return 1;
		}
	};

	var _Window_Options_makeCommandList = Window_Options.prototype.makeCommandList;
	Window_Options.prototype.makeCommandList = function() {
		_Window_Options_makeCommandList.call(this);
		if (M._hide == 0) {
			var set_text = "";
			switch(ConfigManager.langSelect){
				case 0:
					set_text = "言語";
					break;
				case 1:
					set_text = "언어";		// [KO patch] 원본은 "Language"
					break;
				case 2:
					set_text = "语言";
					break;
			}
			this.addCommand( set_text, "langSelect");
		}
	};
	var _Window_Options_statusText = Window_Options.prototype.statusText;
	Window_Options.prototype.statusText = function(index) {
		var symbol = this.commandSymbol(index);
		if (symbol == "langSelect") {
			var return_text = "";
			switch(this.getConfigValue(symbol)){
				case 0:
					return_text = "Japanese";
					break;
				case 1:
					return_text = M._2nd_language;
					break;
				case 2:
					return_text = M._3nd_language;
					break;
			}
			return return_text;
		}
		return _Window_Options_statusText.call(this, index);
	};

	// ----- Switch resource -----

	RTK.terms_change = function(_lang) {
		if (RTK._ready) {
			if (_lang === undefined) {
				_lang = ConfigManager.langSelect;
			} else {
				ConfigManager.langSelect = _lang;
			}
			
			switch(_lang){
				case 0:
					if ($dataSystem.terms != terms_J) {
						$dataSystem.terms = terms_J;
						$dataActors = actors_J;
						$dataClasses = classes_J;
						$dataItems = items_J;
						$dataWeapons = weapons_J;
						$dataArmors = armors_J;
						$dataEnemies = enemies_J;
						$dataTroops = troops_J;
						$dataSkills = skills_J;
						$dataStates = states_J;
						$dataSystem.weaponTypes = t_weapons_J;
						$dataSystem.armorTypes = t_armors_J;
						$dataSystem.equipTypes = t_equips_J;
						$dataSystem.skillTypes = t_skills_J;
						$dataSystem.elements = t_elements_J;
					}
					break;
					
				case 1:
					if ($dataSystem.terms != terms_E) {
						$dataSystem.terms = terms_E;
						$dataActors = actors_E;
						$dataClasses = classes_E;
						$dataItems = items_E;
						$dataWeapons = weapons_E;
						$dataArmors = armors_E;
						$dataEnemies = enemies_E;
						$dataTroops = troops_E;
						$dataSkills = skills_E;
						$dataStates = states_E;
						$dataSystem.weaponTypes = t_weapons_E;
						$dataSystem.armorTypes = t_armors_E;
						$dataSystem.equipTypes = t_equips_E;
						$dataSystem.skillTypes = t_skills_E;
						$dataSystem.elements = t_elements_E;
					}
					break;
				case 2:
					if ($dataSystem.terms != terms_C) {
						$dataSystem.terms = terms_C;
						$dataActors = actors_C;
						$dataClasses = classes_C;
						$dataItems = items_C;
						$dataWeapons = weapons_C;
						$dataArmors = armors_C;
						$dataEnemies = enemies_C;
						$dataTroops = troops_C;
						$dataSkills = skills_C;
						$dataStates = states_C;
						$dataSystem.weaponTypes = t_weapons_C;
						$dataSystem.armorTypes = t_armors_C;
						$dataSystem.equipTypes = t_equips_C;
						$dataSystem.skillTypes = t_skills_C;
						$dataSystem.elements = t_elements_C;
					}
					break;
					break;
			}
			
			
			if (M._variable > 0) {
				//$gameSwitches.setValue(M._variable, _lang);
				$gameVariables.setValue(M._variable, _lang);
			}
			RTK.log(N + ".terms_change (_lang:" + _lang + ")");
		}
	};

	RTK.onStart(function(_mode){
		RTK.terms_change();
		RTK.log(N + " start (mode:" + _mode + ")");
	});
	var _Scene_Title_create = Scene_Title.prototype.create;
	Scene_Title.prototype.create = function() {
		RTK.terms_change();
		_Scene_Title_create.call(this);
	};
	var _Scene_Options_terminate = Scene_Options.prototype.terminate;
	Scene_Options.prototype.terminate = function() {
		_Scene_Options_terminate.call(this);
		RTK.terms_change();
	};

	// ----- Game_Actor support -----
	var _Game_Actor_initMembers = Game_Actor.prototype.initMembers;
	Game_Actor.prototype.initMembers = function() {
		_Game_Actor_initMembers.call(this);
		this[NK + "n_en"] = "";
		this[NK + "nn_en"] = "";
		this[NK + "p_en"] = "";
		
		this[NK + "n_ch"] = "";
		this[NK + "nn_ch"] = "";
		this[NK + "p_ch"] = "";
	};
	var _Game_Actor_setup = Game_Actor.prototype.setup;
	Game_Actor.prototype.setup = function(actorId) {
		_Game_Actor_setup.call(this, actorId);
		if (RTK._ready) {
			this._name = actors_J[this._actorId].name;
			this._nickname = actors_J[this._actorId].nickname;
			this._profile = actors_J[this._actorId].profile;
			this[NK + "n_en"] = actors_E[this._actorId].name;
			this[NK + "nn_en"] = actors_E[this._actorId].nickname;
			this[NK + "p_en"] = actors_E[this._actorId].profile;
			
			this[NK + "n_ch"] = actors_C[this._actorId].name;
			this[NK + "nn_ch"] = actors_C[this._actorId].nickname;
			this[NK + "p_ch"] = actors_C[this._actorId].profile;
		} else {
			this[NK + "n_en"] = this._name;
			this[NK + "nn_en"] = this._nickname;
			this[NK + "p_en"] = this._profile;
		}
	};
	var _Game_Actor_name = Game_Actor.prototype.name;
	Game_Actor.prototype.name = function() {
		_Game_Actor_name.call(this);
		var text = "";
		switch(ConfigManager.langSelect){
			case 0:
				set_text = this._name;
				break;
			case 1:
				set_text = this[NK + "n_en"];
				break;
			case 2:
				set_text = this[NK + "n_ch"];
				break;
		}
		return set_text;
	};
	var _Game_Actor_setName = Game_Actor.prototype.setName;
	Game_Actor.prototype.setName = function(name) {
		var a = name.split(M._separator);
		if (a.length == 2) {
			_Game_Actor_setName.call(this, a[0]);
			this[NK + "n_en"] = a[1];
		} else {
			_Game_Actor_setName.call(this, name);
			this[NK + "n_ch"] = name;
		}
	};
	var _Game_Actor_nickname = Game_Actor.prototype.nickname;
	Game_Actor.prototype.nickname = function() {
		_Game_Actor_nickname.call(this);
		var text = "";
		switch(ConfigManager.langSelect){
			case 0:
				set_text = this._nickname;
				break;
			case 1:
				set_text = this[NK + "nn_en"];
				break;
			case 2:
				set_text = this[NK + "nn_ch"];
				break;
		}
		return set_text;
	};
	var _Game_Actor_setNickname = Game_Actor.prototype.setNickname;
	Game_Actor.prototype.setNickname = function(nickname) {
		var a = nickname.split(M._separator);
		if (a.length == 2) {
			_Game_Actor_setNickname.call(this, a[0]);
			this[NK + "nn_en"] = a[1];
		} else {
			_Game_Actor_setNickname.call(this, nickname);
			this[NK + "nn_ch"] = nickname;
		}
	};
	var _Game_Actor_profile = Game_Actor.prototype.profile;
	Game_Actor.prototype.profile = function() {
		_Game_Actor_profile.call(this);
		var text = "";
		switch(ConfigManager.langSelect){
			case 0:
				set_text = this._profile;
				break;
			case 1:
				set_text = this[NK + "p_en"];
				break;
			case 2:
				set_text = this[NK + "p_ch"];
				break;
		}
		return set_text;
	};
	var _Game_Actor_setProfile = Game_Actor.prototype.setProfile;
	Game_Actor.prototype.setProfile = function(profile) {
		var a = profile.split(M._separator);
		if (a.length == 2) {
			_Game_Actor_setProfile.call(this, a[0]);
			this[NK + "p_en"] = a[1];
		} else {
			_Game_Actor_setProfile.call(this, profile);
			this[NK + "p_ch"] = profile;
		}
	};

	// ----- Terms' default values -----

	/* 
	 * If you use English version of RPG Maker MV, following "terms_E" list will not be used, will be replaced by your words in Terms tab of database tool.
	 * In this case, you only need to update the following "terms_J" list, if you don't like the default Japansese terms settings.
	 * 
	 * もし日本語版のRPGツクールMVを利用している場合、以下に定義されている terms_J 配列は利用されず、データベース機能の用語タブで設定した値で上書きされます。
	 * もし標準の英語表記が好ましくない場合、あなたは以下の terms_E 配列を修正することでゲーム中の英語モードの用語を修正することができます。
	 */

	M._terms_E = {
		"basic":["레벨","Lv","HP","HP","MP","MP","TP","TP","경험치","EXP"],
		"commands":["싸운다","도망친다","공격","방어","아이템","스킬","옷차림","스테이터스","진형","저장","게임 종료","옵션","소지품","옷차림","중요한 것","옷","옷","전부 해제","새 게임","불러오기",null,"타이틀로","취소",null,"구입","판매"],
		"params":["최대 HP","최대 MP","공격력","방어력","마법력","마법 방어","민첩성","운","명중률","회피율"],
		"messages":{"actionFailure":"%1에게는 효과가 없었다!","actorDamage":"%1은(는) %2의 대미지를 입었다!","actorDrain":"%1은(는) %2을(를) %3 빼앗겼다!","actorGain":"%1의 %2이(가) %3 늘어났다!","actorLoss":"%1의 %2이(가) %3 줄어들었다!","actorNoDamage":"%1은(는) 대미지를 입지 않았다!","actorNoHit":"빗나감! %1은(는) 대미지를 입지 않았다!","actorRecovery":"%1의 %2이(가) %3 회복됐다!","alwaysDash":"항상 대시","bgmVolume":"BGM 음량","bgsVolume":"BGV(신음) 음량","buffAdd":"%1의 %2이(가) 올라갔다!","buffRemove":"%1의 %2이(가) 원래대로 돌아왔다!","commandRemember":"커맨드 기억","counterAttack":"%1의 반격!","criticalToActor":"뼈아픈 일격!!","criticalToEnemy":"회심의 일격!!","debuffAdd":"%1의 %2이(가) 내려갔다!","defeat":"%1은(는) 싸움에서 패배했다.","emerge":"%1이(가) 나타났다!","enemyDamage":"%1에게 %2의 대미지를 입혔다!","enemyDrain":"%1의 %2을(를) %3 빼앗았다!","enemyGain":"%1의 %2이(가) %3 늘어났다!","enemyLoss":"%1의 %2이(가) %3 줄어들었다!","enemyNoDamage":"%1에게 대미지를 입히지 못했다!","enemyNoHit":"빗나감! %1에게 대미지를 입히지 못했다!","enemyRecovery":"%1의 %2이(가) %3 회복됐다!","escapeFailure":"하지만 도망칠 수 없었다!","escapeStart":"%1은(는) 도망치기 시작했다!","evasion":"%1은(는) 공격을 피했다!","expNext":"다음 %1까지","expTotal":"현재 %1","file":"파일","levelUp":"%1은(는) %2 %3(으)로 올랐다!","loadMessage":"어느 파일을 불러오시겠습니까?","magicEvasion":"%1은(는) 마법을 무효화했다!","magicReflection":"%1은(는) 마법을 튕겨냈다!","meVolume":"ME 음량","obtainExp":"%1의 %2을(를) 획득!","obtainGold":"돈을 %1\\G 손에 넣었다!","obtainItem":"%1을(를) 손에 넣었다!","obtainSkill":"%1을(를) 익혔다!","partyName":"%1 일행","possession":"소지 수","preemptive":"%1이(가) 선수를 쳤다!","saveMessage":"어느 파일에 저장하시겠습니까?","seVolume":"SE·보이스 음량","substitute":"%1이(가) %2을(를) 감쌌다!","surprise":"%1은(는) 기습을 당했다!","useItem":"%1은(는) %2을(를) 사용했다!","victory":"%1의 승리!"}
	};
	M._terms_J = {
		"basic":["レベル","Lv","ＨＰ","HP","ＭＰ","MP","ＴＰ","TP","経験値","EXP"],
		"commands":["戦う","逃げる","攻撃","防御","アイテム","スキル","装備","ステータス","並び替え","セーブ","ゲーム終了","オプション","武器","防具","大事なもの","装備","最強装備","全て外す","ニューゲーム","コンティニュー",null,"タイトルへ","やめる",null,"購入する","売却する"],
		"params":["最大ＨＰ","最大ＭＰ","攻撃力","防御力","魔法力","魔法防御","敏捷性","運","命中率","回避率"],
		"messages":{"actionFailure":"%1には効かなかった！","actorDamage":"%1は %2 のダメージを受けた！","actorDrain":"%1は%2を %3 奪われた！","actorGain":"%1の%2が %3 増えた！","actorLoss":"%1の%2が %3 減った！","actorNoDamage":"%1はダメージを受けていない！","actorNoHit":"ミス！　%1はダメージを受けていない！","actorRecovery":"%1の%2が %3 回復した！","alwaysDash":"常時ダッシュ","bgmVolume":"BGM 音量","bgsVolume":"BGS 音量","buffAdd":"%1の%2が上がった！","buffRemove":"%1の%2が元に戻った！","commandRemember":"コマンド記憶","counterAttack":"%1の反撃！","criticalToActor":"痛恨の一撃！！","criticalToEnemy":"会心の一撃！！","debuffAdd":"%1の%2が下がった！","defeat":"%1は戦いに敗れた。","emerge":"%1が出現！","enemyDamage":"%1に %2 のダメージを与えた！","enemyDrain":"%1の%2を %3 奪った！","enemyGain":"%1の%2が %3 増えた！","enemyLoss":"%1の%2が %3 減った！","enemyNoDamage":"%1にダメージを与えられない！","enemyNoHit":"ミス！　%1にダメージを与えられない！","enemyRecovery":"%1の%2が %3 回復した！","escapeFailure":"しかし逃げることはできなかった！","escapeStart":"%1は逃げ出した！","evasion":"%1は攻撃をかわした！","expNext":"次の%1まで","expTotal":"現在の%1","file":"File","levelUp":"%1は%2 %3 に上がった！","loadMessage":"どのファイルをロードしますか？","magicEvasion":"%1は魔法を打ち消した！","magicReflection":"%1は魔法を跳ね返した！","meVolume":"ME 音量","obtainExp":"%1 の%2を獲得！","obtainGold":"お金を %1\\G 手に入れた！","obtainItem":"%1を手に入れた！","obtainSkill":"%1を覚えた！","partyName":"%1たち","possession":"持っている数","preemptive":"%1は先手を取った！","saveMessage":"どのファイルにセーブしますか？","seVolume":"SE 音量","substitute":"%1が%2をかばった！","surprise":"%1は不意をつかれた！","useItem":"%1は%2を使った！","victory":"%1の勝利！"}
	};
	
	M._terms_C = {
		"basic":["レベル","Lv","ＨＰ","HP","ＭＰ","MP","ＴＰ","TP","経験値","EXP"],
		"commands":["戦う","逃げる","攻撃","防御","物品","スキル","衣服","狀態","並び替え","保存","結束","設置","持有","服裝","大事なもの","衣服","衣服","全て外す","新遊戲","載入",null,"回到主菜單","取消",null,"購入する","賣出"],
		"params":["最大ＨＰ","最大ＭＰ","攻撃力","防御力","魔法力","魔法防御","敏捷性","運","命中率","回避率"],
		"messages":{"actionFailure":"%1には効かなかった！","actorDamage":"%1は%2のダメージを受けた！","actorDrain":"%1は%2を%3奪われた！","actorGain":"%1の%2が%3増えた！","actorLoss":"%1の%2が%3減った！","actorNoDamage":"%1はダメージを受けていない！","actorNoHit":"ミス！　%1はダメージを受けていない！","actorRecovery":"%1の%2が%3回復した！","alwaysDash":"常用設置","bgmVolume":"BGM音量","bgsVolume":"BGV（娇喘声）音量","buffAdd":"%1の%2が上がった！","buffRemove":"%1の%2が元に戻った！","commandRemember":"コマンド記憶","counterAttack":"%1の反撃！","criticalToActor":"痛恨の一撃！！","criticalToEnemy":"会心の一撃！！","debuffAdd":"%1の%2が下がった！","defeat":"%1は戦いに敗れた。","emerge":"%1が出現！","enemyDamage":"%1に%2のダメージを与えた！","enemyDrain":"%1の%2を%3奪った！","enemyGain":"%1の%2が%3増えた！","enemyLoss":"%1の%2が%3減った！","enemyNoDamage":"%1にダメージを与えられない！","enemyNoHit":"ミス！　%1にダメージを与えられない！","enemyRecovery":"%1の%2が%3回復した！","escapeFailure":"しかし逃げることはできなかった！","escapeStart":"%1は逃げ出した！","evasion":"%1は攻撃をかわした！","expNext":"次の%1まで","expTotal":"現在の%1","file":"File","levelUp":"%1は%2%3に上がった！","loadMessage":"儲存到哪個存檔呢？","magicEvasion":"%1は魔法を打ち消した！","magicReflection":"%1は魔法を跳ね返した！","meVolume":"ME音量","obtainExp":"%1の%2を獲得！","obtainGold":"お金を%1\\G手に入れた！","obtainItem":"%1を手に入れた！","obtainSkill":"%1を覚えた！","partyName":"%1たち","possession":"持っている数","preemptive":"%1は先手を取った！","saveMessage":"储存到哪个存档呢？","seVolume":"SEVoice音量","substitute":"%1が%2をかばった！","surprise":"%1は不意をつかれた！","useItem":"%1は%2を使った！","victory":"%1の勝利！"}
	};

	// ----- Translated values -----
	//
	// This section will support to integrate and control translated texts in bulk.
	// If you need to ask someone to translate game terms, this section's function and data structure will support you.
	//
	// ここでは主に大規模なゲーム用に、翻訳用のデータをまとめて管理する方法を提供します。
	// もしゲーム用語の翻訳を別の誰かに依頼するのなら、このセクションにある関数とデータ構造が助けになるでしょう。

	M.writeTranslationBase = function() {
		var ret = {
			"actors" : $dataActors.map(function(o){return o ? [o.name, o.nickname, o.profile] : null}).splice(1),
			"classes" : $dataClasses.map(function(o){return o ? o.name : null}).splice(1),
			"items" : $dataItems.map(function(o){return o ? [o.name, o.description] : null}).splice(1),
			"weapons" : $dataWeapons.map(function(o){return o ? [o.name, o.description] : null}).splice(1),
			"armors" : $dataArmors.map(function(o){return o ? [o.name, o.description] : null}).splice(1),
			"enemies" : $dataEnemies.map(function(o){return o ? o.name : null}).splice(1),
			"troops" : $dataTroops.map(function(o){return o ? o.name : null}).splice(1),
			"skills" : $dataSkills.map(function(o){return o ? [o.name, o.description] : null}).splice(1),
			"states" : $dataStates.map(function(o){return o ? o.name : null}).splice(1),
			"t_weapons" : $dataSystem.weaponTypes.map(function(o){return o;}).splice(1),
			"t_armors" : $dataSystem.armorTypes.map(function(o){return o;}).splice(1),
			"t_equips" : $dataSystem.equipTypes.map(function(o){return o;}).splice(1),
			"t_skills" : $dataSystem.skillTypes.map(function(o){return o;}).splice(1),
			"t_elements" : $dataSystem.elements.map(function(o){return o;}).splice(1)
		};
		var json = JsonEx.stringify(ret);
		RTK.writeFileSync("translation_base.json", json, true);
	};
	M.applyTranslation = function(o) {
		if (o) {
			RTK.cloneObject(o, M.translation);
		}
	};

	/*
	 * You can use String, String list or Object in each translation Array.
	 *	String - It overwrites the name attribute of the target data object.
	 *	String list - Its elements overwrite the target data object. It depends on target type.
	 *		Actor: name, nickname, profile, note
	 * 		Others: name, description, note
	 *	Object - Its attributes overwrite the target data object.
	 *
	 * Example (English data):
	 * 	M.translation.actors = ["Harold", "Therese", "Marsha", "Lucius"];
	 * 	M.translation.actors = [["Harold","Sword boy"], ["Therese","Axe girl","Teenage girl with green hair loves Axe."], "Marsha", "Lucius"];
	 *	M.translation.classes = ["Hero", "Warrior", "Mage", "Priest"];
	 *
	 * Hint: The object's "id" attribute will affect the fetch function.
	 * 	It means you can skip elements with id attribute, as follows;
	 * 	var actors = ["name of 1st actor", {"name":"name of 100th actor","id":100}, ["name of 101th actor,nickname of 101th actor"]];
	*/

	M.translation = {
		"actors":[],
		"classes":[],
		"items":[],
		"weapons":[],
		"armors":[],
		"enemies":[],
		"troops":[],
		"skills":[],
		"states":[],
		"t_weapons":[],
		"t_armors":[],
		"t_equips":[],
		"t_skills":[],
		"t_elements":[]
	};

})(this);

