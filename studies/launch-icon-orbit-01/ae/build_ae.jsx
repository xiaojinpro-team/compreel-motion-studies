// Icon Cloud Intro · After Effects builder (MIT): reads ae_data.json (3D values converted from the web keyframes) and builds the project.
// File → Scripts → Run Script File… with this file; keep textures/ next to it.
// Camera zoom = focal of a 40° vertical FOV, position (960,540,-D) looking at (960,540,0); each icon is a 3D layer; the rush (frames 55–57) uses a motion-blurred copy.
(function () {
  app.beginSuppressDialogs();
  try {
  var here = File($.fileName).parent.fsName;
  var root = Folder(here).parent.fsName;
  function readJSON(p) { var f = new File(p); f.encoding = "UTF-8"; f.open("r"); var s = f.read(); f.close(); return eval("(" + s + ")"); }
  var D = readJSON(here + "/ae_data.json");
  var fps = D.fps, W = D.size[0], H = D.size[1];
  app.beginUndoGroup("build icon cloud intro");
  if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
  var proj = app.newProject();
  var comp = app.project.items.addComp("Icon Cloud Intro", W, H, 1, 100 / fps, fps);
  comp.bgColor = [243 / 255, 243 / 255, 245 / 255];
  var folder = app.project.items.addFolder("textures");
  var times = []; for (var i = 0; i < D.times.length; i++) times.push(D.times[i] / fps);
  var cache = {};
  function footage(name) {
    if (cache[name]) return cache[name];
    var it = app.project.importFile(new ImportOptions(new File(here + "/textures/" + name))); it.parentFolder = folder; cache[name] = it; return it;
  }
  function linearize(prop, spatial) {
    for (var k = 1; k <= prop.numKeys; k++) {
      prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
      if (spatial) { prop.setSpatialAutoBezierAtKey(k, false); prop.setSpatialContinuousAtKey(k, false); prop.setSpatialTangentsAtKey(k, [0, 0, 0], [0, 0, 0]); }
    }
  }
  var bg = comp.layers.addSolid([243 / 255, 243 / 255, 245 / 255], "background #F3F3F5", W, H, 1); bg.locked = true;
  var titles = [];
  for (var li = 0; li < D.layers.length; li++) {
    var L = D.layers[li];
    if (L.kind === "plate") {
      var g = comp.layers.add(footage(L.texture)); g.name = "title gradient";
      var ov = []; for (var i = 0; i < L.samples.length; i++) ov.push(L.samples[i][0]);
      g.property("ADBE Transform Group").property("ADBE Opacity").setValuesAtTimes(times, ov); linearize(g.property("ADBE Transform Group").property("ADBE Opacity"), false);
    }
  }
  var cam = comp.layers.addCamera("Camera", [W / 2, H / 2]);
  cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(D.zoom);
  cam.property("ADBE Transform Group").property("ADBE Anchor Point").setValue([W / 2, H / 2, 0]);
  var cp = []; for (var i = 0; i < D.camera.length; i++) cp.push([W / 2, H / 2, D.camera[i]]);
  var camPos = cam.property("ADBE Transform Group").property("ADBE Position"); camPos.setValuesAtTimes(times, cp); linearize(camPos, true);
  for (var li = 0; li < D.layers.length; li++) {
    var L = D.layers[li]; if (L.kind !== "card") continue;
    var ly = comp.layers.add(footage(L.texture)); ly.name = (L.id === "icon" ? "CENTER ICON" : "slot " + L.id) + " · " + L.texture; ly.threeDLayer = true;
    var tg = ly.property("ADBE Transform Group");
    tg.property("ADBE Anchor Point").setValue([L.anchor[0], L.anchor[1], 0]);
    tg.property("ADBE Scale").setValue([L.scale, L.scale, L.scale]);
    var pv = [], rv = [], ov = [];
    for (var i = 0; i < L.samples.length; i++) { var s = L.samples[i]; pv.push([s[0], s[1], s[2]]); rv.push(s[3]); ov.push(s[4]); }
    tg.property("ADBE Position").setValuesAtTimes(times, pv); linearize(tg.property("ADBE Position"), true);
    tg.property("ADBE Rotate Z").setValuesAtTimes(times, rv); linearize(tg.property("ADBE Rotate Z"), false);
    tg.property("ADBE Opacity").setValuesAtTimes(times, ov); linearize(tg.property("ADBE Opacity"), false);
    // rush (frames 55-57) uses a motion-blurred copy; the main layer stops at 55
    var mb = ly.duplicate(); mb.name = ly.name + " · rush blur"; mb.motionBlur = true; mb.inPoint = 55 / fps; mb.outPoint = 58 / fps;
    ly.outPoint = 55 / fps;
  }
  comp.motionBlur = true; comp.shutterAngle = 216; comp.shutterPhase = -108; comp.motionBlurSamplesPerFrame = 32; comp.motionBlurAdaptiveSampleLimit = 128;
  var cfg = readJSON(here + "/title_config.json");
  for (var li = 0; li < D.layers.length; li++) {
    var L = D.layers[li]; if (L.kind !== "text") continue;
    var c = L.id === "title_line1" ? cfg.line1 : cfg.line2;
    var tl = comp.layers.addText(c.text); tl.name = L.id === "title_line1" ? "TITLE line 1" : "TITLE line 2 (product name)";
    var st = tl.property("ADBE Text Properties").property("ADBE Text Document"); var td = st.value;
    td.resetCharStyle(); td.font = cfg.font; td.fontSize = cfg.fontSize; td.applyFill = true; td.fillColor = c.color; td.applyStroke = false; td.justification = ParagraphJustification.CENTER_JUSTIFY; st.setValue(td);
    var r = tl.sourceRectAtTime(0, false);
    tl.property("ADBE Transform Group").property("ADBE Anchor Point").setValue([r.left + r.width / 2, r.top + r.height / 2]);
    var pv = [], ov = []; for (var i = 0; i < L.samples.length; i++) { pv.push([L.samples[i][0], L.samples[i][1] + (c.dy || 0)]); ov.push(L.samples[i][2]); }
    var tp = tl.property("ADBE Transform Group").property("ADBE Position"); tp.setValuesAtTimes(times, pv); linearize(tp, false);
    var to = tl.property("ADBE Transform Group").property("ADBE Opacity"); to.setValuesAtTimes(times, ov); linearize(to, false);
  }
  app.endUndoGroup();
  app.project.save(new File(here + "/icon-cloud-intro.aep"));
  var log = new File(here + "/build_ae.log"); log.open("w"); log.write("BUILD OK " + comp.numLayers + " layers"); log.close();
  } catch (e) { var lg = new File(File($.fileName).parent.fsName + "/build_ae.log"); lg.open("w"); lg.write("ERROR line " + e.line + ": " + e.toString()); lg.close(); }
  app.endSuppressDialogs(false);
})();
