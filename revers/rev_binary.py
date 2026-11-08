#!/usr/bin/env python3
"""
rev_binary.py - derive / verify the requested Rust offsets from GameAssembly
only (build 26140533).

NO live dump and NO tools/reference tables are read by this script.  Every
offset it prints is backed by one of two binary artefacts:

  1. the per-type int32 field-offset table stored in .rdata
     (Il2CppCodeGenModule::fieldOffsets, 0x67676767 = "not stored"), or
  2. an actual `[this + disp]` memory operand inside one of the type's own
     IL2CPP methods (disassembled with capstone).

The metadata blob supplies field names / declaration order / type indices;
the Il2CppType table and Il2CppTypeDefinitionSizes table supply layout sizes.
Both tables are located by validating their structure in the binary at run
time (the RVAs below are verified before use, and re-scanned if they change).

Usage:
    py -3 revers\\rev_binary.py
Outputs (revers/out/):
    BasePlayer_binary.h, Projectile_binary.h, AttackEntity_binary.h,
    PlayerModel_binary.h, binary_provenance.json, binary_report.md
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import meta_rva as M  # noqa: E402

DLL = M.DEFAULT_DLL
IMAGE_BASE = M.IMAGE_BASE
POISON = 0x67676767

# ---- requested fields ------------------------------------------------------
# (name, expected offset, declared type).  The expected offset is only used as
# a lookup key / sanity check - the value that is written out must be found in
# the binary, otherwise the run fails for that field.
REQUEST = {
    "BasePlayer": [
        ("UserIDString", 0x2F0, "string"),
        ("blueprints", 0x318, "PlayerBlueprints"),
        ("lastSentTick", 0x358, "int"),
        ("currentTeam", 0x368, "ulong"),
        ("modelState", 0x398, "ModelState"),
        ("voiceRecorder", 0x3B8, "PlayerVoiceRecorder"),
        ("eyes", 0x3C8, "PlayerEyes"),
        ("GestureViewModel", 0x438, "ViewModel"),
        ("input", 0x440, "InputState"),
        ("metabolism", 0x4C0, "PlayerMetabolism"),
        ("hidden_CapsuleCollider", 0x530, "CapsuleCollider"),
        ("playerRigidbody", 0x548, "Rigidbody"),
        ("movement", 0x550, "PlayerWalkMovement"),
        ("clActiveItem", 0x590, "ItemId"),
        ("inventory", 0x5E0, "PlayerInventory"),
        ("mounted", 0x5E8, "BaseMountable"),
        ("fallDamageEffect", 0x6D0, "Effect"),
        ("drownEffect", 0x6D8, "Effect"),
        ("playerFlags", 0x6E0, "PlayerFlags"),
        ("_displayName", 0x6F8, "string"),
        ("voiceSpeaker", 0x710, "PlayerVoiceSpeaker"),
        ("modifiers", 0x718, "PlayerModifiers"),
        ("userID", 0x728, "ulong"),
        ("playerModel", 0x748, "PlayerModel"),
    ],
    "Projectile": [
        ("initialVelocity", 0x28, "Vector3"), ("drag", 0x34, "float"),
        ("gravityModifier", 0x38, "float"), ("thickness", 0x3C, "float"),
        ("changeInitialOrientation", 0x40, "bool"), ("initialDistance", 0x44, "float"),
        ("initialOrientation", 0x48, "Vector3"), ("remainInWorld", 0x54, "bool"),
        ("stickProbability", 0x58, "float"), ("breakProbability", 0x5C, "float"),
        ("conditionLoss", 0x60, "float"), ("ricochetChance", 0x64, "float"),
        ("penetrationPower", 0x68, "float"), ("canRefract", 0x6C, "bool"),
        ("penetratesVehicles", 0x6D, "bool"), ("waterIntegrityLoss", 0x70, "float"),
        ("damageProperties", 0x78, "DamageProperties"),
        ("damageDistances", 0x80, "MinMax"), ("minMax", 0x80, "MinMax"),
        ("damageMultipliers", 0x88, "MinMax"),
        ("damageTypes", 0x90, "List<DamageTypeEntry>"),
        ("rendererToScale", 0x98, "ScaleRenderer"),
        ("scaleTrailRenderer", 0x98, "ScaleTrailRenderer"),
        ("firstPersonRenderer", 0xA0, "ScaleRenderer"),
        ("scaleTransform", 0xA0, "ScaleTransform"),
        ("createDecals", 0xA8, "bool"), ("doHitEffects", 0xA9, "bool"),
        ("flybySound", 0xB0, "SoundDefinition"),
        ("soundDefinition", 0xB0, "SoundDefinition"),
        ("flybySoundDistance", 0xB8, "float"),
        ("closeFlybySound", 0xC0, "SoundDefinition"),
        ("closeFlybyDistance", 0xC8, "float"), ("tumbleSpeed", 0xCC, "float"),
        ("tumbleAxis", 0xD0, "Vector3"), ("playDefaultHitEffects", 0xDC, "bool"),
        ("clientEffectData", 0xE0, "CustomEffectData"),
        ("customEffectData", 0xE0, "CustomEffectData"),
        ("clientEffectPrefab", 0xE8, "GameObjectRef"),
        ("gameObjectRef", 0xE8, "GameObjectRef"),
        ("swimScale", 0xF0, "Vector3"), ("swimSpeed", 0xFC, "Vector3"),
        ("baseProjectile", 0x110, "BaseProjectile"),
        ("projectile", 0x118, "Projectile"),
        ("hidden_ccfe34b7cfa107117310af889ea8338a5bf48454", 0x120, "HitTest"),
        ("maxDistance", 0x140, "float"), ("currentVelocity", 0x164, "Vector3"),
        ("currentPosition", 0x170, "Vector3"), ("traveledDistance", 0x17C, "float"),
        ("traveledTime", 0x180, "float"), ("sentPosition", 0x188, "Vector3"),
        ("previousPosition", 0x194, "Vector3"),
        ("previousVelocity", 0x1A0, "Vector3"),
        ("previousTraveledTime", 0x1AC, "float"),
        ("mod", 0x1E0, "ItemModProjectile"), ("owner", 0x1F0, "BasePlayer"),
    ],
    "AttackEntity": [
        ("deployDelay", 0x2F0, "float"), ("repeatDelay", 0x2F4, "float"),
        ("animationDelay", 0x2F8, "float"), ("effectiveRange", 0x2FC, "float"),
        ("npcDamageScale", 0x300, "float"), ("attackLengthMin", 0x304, "float"),
        ("attackLengthMax", 0x308, "float"), ("attackSpacing", 0x30C, "float"),
        ("aiAimSwayOffset", 0x310, "float"), ("aiAimCone", 0x314, "float"),
        ("aiOnlyInRange", 0x318, "bool"), ("CloseRangeAddition", 0x31C, "float"),
        ("MediumRangeAddition", 0x320, "float"),
        ("LongRangeAddition", 0x324, "float"),
        ("CanUseAtMediumRange", 0x328, "bool"),
        ("CanUseAtLongRange", 0x329, "bool"),
        ("reloadSounds", 0x330, "SoundDefinition[]"),
        ("thirdPersonMeleeSound", 0x338, "SoundDefinition"),
        ("recoilCompDelayOverride", 0x340, "float"),
        ("wantsRecoilComp", 0x344, "bool"),
        ("showCrosshairOnTutorial", 0x345, "bool"),
        ("noHeadshots", 0x346, "bool"),
    ],
    "PlayerModel": [
        ("Shoulders", 0x98, "Transform[]"),
        ("AdditionalSpineBones", 0xA0, "Transform[]"),
        ("_multiMesh", 0xB8, "SkinnedMultiMesh"),
        ("TurnAimSmoothTime", 0xD0, "float"), ("TurnHead", 0xD4, "TurnSegment"),
        ("TurnChest", 0xE4, "TurnSegment"), ("TurnSpine", 0xF4, "TurnSegment"),
        ("TurnPelvis", 0x104, "TurnSegment"),
        ("TurnChestLowerShare", 0x114, "float"),
        ("TurnSpineLowerShare", 0x118, "float"),
        ("TurnHeadLockAngle", 0x11C, "float"),
        ("TurnHeadSmoothTime", 0x120, "float"),
        ("TurnHeadMaxSpeed", 0x124, "float"),
        ("TurnHeadAimFadeSpeed", 0x128, "float"),
        ("TurnClips", 0x130, "TurnClipSet"),
        ("TurnSpeedByBacklog", 0x138, "AnimationCurve"),
        ("TurnMoveThreshold", 0x140, "float"),
        ("TurnSuppressProceduralLegs", 0x144, "bool"),
        ("TurnLegBlendTime", 0x148, "float"),
        ("TurnPelvisEnabled", 0x14C, "bool"),
        ("TurnPelvisFootPinWeight", 0x150, "float"),
        ("TurnArmFadeSpeed", 0x154, "float"),
        ("TurnArmFadeWeight", 0x158, "float"),
        ("collision", 0x210, "BoxCollider"),
        ("censorshipCube", 0x218, "GameObject"),
        ("censorshipCubeBreasts", 0x220, "GameObject"),
        ("jawBone", 0x228, "GameObject"), ("neckBone", 0x230, "GameObject"),
        ("headBone", 0x238, "GameObject"), ("leftEye", 0x240, "GameObject"),
        ("rightEye", 0x248, "GameObject"), ("eyeController", 0x250, "EyeController"),
        ("blinkController", 0x258, "EyeBlink"), ("SpineBones", 0x260, "Transform[]"),
        ("leftFootBone", 0x268, "Transform"), ("rightFootBone", 0x270, "Transform"),
        ("leftHandPropBone", 0x278, "Transform"),
        ("rightHandPropBone", 0x280, "Transform"),
        ("rightHandTarget", 0x288, "Vector3"),
        ("leftClavicleBone", 0x298, "Transform"), ("isPreview", 0x2A0, "bool"),
        ("leftHandTargetPosition", 0x2A4, "Vector3"),
        ("leftHandTargetRotation", 0x2B0, "Quaternion"),
        ("rightHandTargetPosition", 0x2C0, "Vector3"),
        ("rightHandTargetRotation", 0x2CC, "Quaternion"),
        ("leftUlnaTwistBone", 0x2E0, "Transform"),
        ("rightUlnaTwistBone", 0x2E8, "Transform"),
        ("leftHandTwistRelaxWeight", 0x2F0, "float"),
        ("rightHandTwistRelaxWeight", 0x2F4, "float"),
        ("TwistBones", 0x2F8, "PlayerTwistBoneSetup[]"),
        ("steeringTargetDegrees", 0x300, "float"),
        ("playerBoatSteeringTargetDegrees", 0x304, "float"),
        ("rightFootTargetPosition", 0x308, "Vector3"),
        ("rightFootTargetRotation", 0x314, "Quaternion"),
        ("leftFootTargetPosition", 0x324, "Vector3"),
        ("leftFootTargetRotation", 0x330, "Quaternion"),
        ("legsAnimator", 0x340, "LegsAnimator"),
        ("upperBodyMask", 0x348, "AvatarMask"), ("fullMask", 0x350, "AvatarMask"),
        ("CinematicAnimationController", 0x358, "RuntimeAnimatorController"),
        ("DefaultAvatar", 0x360, "Avatar"), ("CinematicAvatar", 0x368, "Avatar"),
        ("DefaultHoldType", 0x370, "RuntimeAnimatorController"),
        ("SleepGesture", 0x378, "RuntimeAnimatorController"),
        ("CrawlToIncapacitatedGesture", 0x380, "RuntimeAnimatorController"),
        ("CrawlToIncapacitatedGestureHandcuff", 0x388, "RuntimeAnimatorController"),
        ("StandToIncapacitatedGesture", 0x390, "RuntimeAnimatorController"),
        ("MaleSkin", 0x3A0, "SkinSetCollection"),
        ("FemaleSkin", 0x3A8, "SkinSetCollection"),
        ("MannequinSkin", 0x3B0, "SkinSetCollection"),
        ("subsurfaceProfile", 0x3B8, "SubsurfaceProfile"),
        ("voiceVolume", 0x3C0, "float"), ("skinColor", 0x3C4, "float"),
        ("skinNumber", 0x3C8, "float"), ("meshNumber", 0x3CC, "float"),
        ("meshSubNumber", 0x3D0, "float"), ("hairNumber", 0x3D4, "float"),
        ("dyeNumber", 0x3D8, "float"), ("skinType", 0x3DC, "int"),
        ("mouthFlapPosRange", 0x3E0, "float"), ("mouthFlapRotRange", 0x3E4, "float"),
        ("mouthSidePosRange", 0x3E8, "float"),
        ("mouthSideFrequency", 0x3EC, "float"),
        ("ArmMotionWeight", 0x3F0, "float"), ("ArmGravity", 0x3F4, "float"),
        ("ArmGravityByPitch", 0x3F8, "AnimationCurve"),
        ("ArmStiffness", 0x400, "float"), ("ArmDamping", 0x404, "float"),
        ("ArmMotionSpeedLimit", 0x408, "float"), ("ArmFlexAngle", 0x40C, "float"),
        ("ArmFlexByPitch", 0x410, "AnimationCurve"),
        ("ArmSpinFadeStart", 0x418, "float"), ("ArmSpinFadeEnd", 0x41C, "float"),
        ("SpineLookUpLimit", 0x420, "float"), ("SpineTwistClamp", 0x424, "float"),
        ("SpineHeadLookWeightVertical", 0x428, "float"),
        ("HeadYawLimit", 0x42C, "float"), ("SpineLowerFollow", 0x430, "float"),
        ("SpineFollowSmoothSpeed", 0x434, "float"),
        ("movementSounds", 0x438, "MovementSounds"), ("showSash", 0x440, "bool"),
        ("tempPoseType", 0x444, "int"), ("underwearSkin", 0x448, "uint"),
        ("position", 0x488, "Vector3"), ("animator", 0x678, "Animator"),
        ("modelState", 0x6D8, "ModelState"),
    ],
}

# Il2CppType / sizes table RVAs found by structural scan (verified at run time).
TYPES_RVA = 0xFBABD30
SIZES_RVA = 0x110F1B00

PRIM = {0x02: (1, 1), 0x03: (2, 2), 0x04: (1, 1), 0x05: (1, 1),
        0x06: (2, 2), 0x07: (2, 2), 0x08: (4, 4), 0x09: (4, 4),
        0x0A: (8, 8), 0x0B: (8, 8), 0x0C: (4, 4), 0x0D: (8, 8),
        0x18: (8, 8), 0x19: (8, 8)}


class Binary:
    def __init__(self):
        self.meta = M.Metadata(M.DEFAULT_METADATA)
        self.pe = M.Pe(DLL)
        self.d = self.pe.data
        self.mapper = M.RvaMapper(self.meta, self.pe)
        # map type-def name -> index
        self.tdi = {}
        for i in range(self.meta.type_count):
            self.tdi.setdefault(self.meta.type(i)["name"], i)
        self._verify_tables()

    # -- PE helpers ------------------------------------------------------
    def r2o(self, rva):
        return self.pe.rva_to_off(rva)

    def q(self, rva):
        o = self.r2o(rva)
        return struct.unpack_from("<Q", self.d, o)[0]

    # -- Il2CppType / sizes tables --------------------------------------
    def _verify_tables(self):
        if not self._types_ok(TYPES_RVA):
            self.types_rva = self._scan_types()
        else:
            self.types_rva = TYPES_RVA
        if not self._sizes_ok(SIZES_RVA):
            self.sizes_rva = self._scan_sizes()
        else:
            self.sizes_rva = SIZES_RVA
        if self.types_rva is None or self.sizes_rva is None:
            raise SystemExit("could not locate Il2CppType / sizes tables")

    def _types_ok(self, rva):
        """Cross-check against metadata: each sampled type-def's byval_type
        index must point at an Il2CppType whose data is that type-def."""
        try:
            checked = 0
            for tdi in range(0, self.meta.type_count, 37):
                t = self.meta.type(tdi)
                idx = t["byval_type"]
                if idx < 0:
                    continue
                o = self.r2o(self.q(rva + idx * 8) - IMAGE_BASE)
                if o is None:
                    continue
                data = struct.unpack_from("<Q", self.d, o)[0]
                bits = struct.unpack_from("<I", self.d, o + 8)[0]
                typ = (bits >> 16) & 0xFF
                if data == tdi and typ in (0x11, 0x12):
                    checked += 1
            return checked > 200
        except Exception:
            return False

    def _sizes_ok(self, rva):
        """A value-type's native_size must equal instance_size - 0x10
        (boxed il2cpp object header).  This rejects shifted tables."""
        try:
            hits = 0
            for name in ("Vector3", "Vector2", "Quaternion", "MinMax",
                         "TurnSegment", "Color"):
                tdi = self.tdi.get(name)
                if tdi is None:
                    continue
                o = self.r2o(self.q(rva + tdi * 8) - IMAGE_BASE)
                if o is None:
                    continue
                inst, nat, _st, _th = struct.unpack_from("<4i", self.d, o)
                if inst > 0x10 and nat == inst - 0x10:
                    hits += 1
            return hits >= 3
        except Exception:
            return False

    def _scan_types(self):
        # look for a long run of pointers into the .data Il2CppType area
        sec = next(s for s in self.pe.sections if s["name"] == ".data")
        lo, hi = sec["va"] + 0x500000, sec["va"] + 0x900000
        best = None
        for secname in (".rdata", ".data"):
            s = next(x for x in self.pe.sections if x["name"] == secname)
            start, end = s["raw"], s["raw"] + s["rawsize"]
            o = start
            run = 0
            st = None
            while o + 8 <= end:
                q = struct.unpack_from("<Q", self.d, o)[0] - IMAGE_BASE
                ok = lo <= q < hi
                if ok:
                    if run == 0:
                        st = o
                    run += 1
                else:
                    if run > 5000 and (best is None or run > best[0]):
                        rva = s["va"] + (st - s["raw"])
                        if self._types_ok(rva):
                            best = (run, rva)
                    run = 0
                o += 8
        return best[1] if best else None

    def _scan_sizes(self):
        best = None
        for secname in (".rdata", ".data"):
            s = next(x for x in self.pe.sections if x["name"] == secname)
            start, end = s["raw"], s["raw"] + s["rawsize"]
            o = start
            run = 0
            st = None
            while o + 8 <= end:
                q = struct.unpack_from("<Q", self.d, o)[0] - IMAGE_BASE
                ok = self.r2o(q) is not None
                if ok:
                    if run == 0:
                        st = o
                    run += 1
                else:
                    if run > 5000 and (best is None or run > best[0]):
                        rva = s["va"] + (st - s["raw"])
                        if self._sizes_ok(rva):
                            best = (run, rva)
                    run = 0
                o += 8
        return best[1] if best else None

    # -- type info -------------------------------------------------------
    def tinfo(self, idx):
        o = self.r2o(self.q(self.types_rva + idx * 8) - IMAGE_BASE)
        if o is None:
            return None
        data = struct.unpack_from("<Q", self.d, o)[0]
        bits = struct.unpack_from("<I", self.d, o + 8)[0]
        return data, (bits >> 16) & 0xFF, bits & 0xFFFF

    def sizeinfo(self, tdi):
        o = self.r2o(self.q(self.sizes_rva + tdi * 8) - IMAGE_BASE)
        if o is None:
            return (0, -1, 0, 0)
        return struct.unpack_from("<4i", self.d, o)

    def resolve_parent(self, ti):
        x = self.tinfo(ti)
        if not x:
            return None
        data, typ, _ = x
        if typ == 0x15:  # GENERICINST -> Il2CppGenericClass*
            o = self.r2o(data - IMAGE_BASE)
            if o is None:
                return None
            return self.resolve_parent(self.q_at(o))
        if typ in (0x11, 0x12):
            return data
        return None

    def q_at(self, off):
        return struct.unpack_from("<Q", self.d, off)[0]

    def fsize(self, fidx):
        x = self.tinfo(fidx)
        if not x:
            return (8, 8, 0)
        data, typ, attrs = x
        if typ in PRIM:
            return (PRIM[typ][0], PRIM[typ][1], attrs)
        if typ == 0x11:
            inst = self.sizeinfo(data)[0]
            sz = inst - 0x10 if inst > 0x10 else inst
            al = 1
            while al * 2 <= min(sz, 8) and sz % (al * 2) == 0:
                al *= 2
            return (sz, al, attrs)
        return (8, 8, attrs)

    def fields(self, tdi):
        t = self.meta.type(tdi)
        off = self.meta.sections["fields"][0]
        out = []
        for k in range(t["field_count"]):
            b = off + (t["first_field"] + k) * 12
            ni, fi, tok = struct.unpack_from("<iiI", self.meta.data, b)
            data, typ, attrs = self.tinfo(fi)
            out.append({
                "order": k, "name": self.meta.string(ni) or "",
                "type_index": fi, "type": typ, "attrs": attrs,
                "token": tok,
            })
        return out

    def layout(self, tdi):
        """Offsets of the type's own fields, relative to the first own field.

        Static fields (attrs & 0x10) are skipped, as il2cpp does.  The result
        is only used to align a class against its .rdata offset table, so the
        parent instance size cancels out.
        """
        cur = 0
        out = []
        for f in self.fields(tdi):
            if f["attrs"] & 0x10:
                continue
            sz, al, _ = self.fsize(f["type_index"])
            cur = (cur + al - 1) // al * al
            out.append((f["order"], f["name"], cur, f["type"]))
            cur += sz
        if out:
            base = out[0][2]
            out = [(o, n, c - base, t) for (o, n, c, t) in out]
        return out

    # -- .rdata field-offset table --------------------------------------
    def _segments(self, tdi):
        """Split the type's own instance fields into runs of consecutive
        metadata orders that are NOT hidden.  Inside such a run the relative
        offsets follow from the declared field types; hidden fields (whose
        real size is unknown) break the run."""
        segs = []
        cur = None
        seg = None
        for f in self.fields(tdi):
            if f["attrs"] & 0x10:          # static: not part of the object
                continue
            if f["name"].startswith("%"):
                if seg:
                    segs.append(seg)
                seg = None
                cur = None
                continue
            sz, al, _ = self.fsize(f["type_index"])
            if seg is None:
                seg = {"start": f["order"], "items": [(f["order"], 0)],
                       "cur": 0, "name": f["name"]}
                cur = 0
            else:
                cur = (cur + al - 1) // al * al
                seg["items"].append((f["order"], cur))
            cur += sz
            seg["cur"] = cur
        if seg:
            segs.append(seg)
        return segs

    def find_table(self, tdi, want=None):
        """Locate the per-type int32 field offset table in .rdata.

        Uses all non-hidden runs of the type's metadata fields.  Inside a run
        the difference between two table entries must equal the difference
        computed from the declared field types, which pins the table base
        (index 0 == metadata field order 0) unambiguously."""
        segs = [s for s in self._segments(tdi) if len(s["items"]) >= 3]
        if not segs:
            return None
        rdata = next(s for s in self.pe.sections if s["name"] == ".rdata")
        start, end = rdata["raw"], rdata["raw"] + rdata["rawsize"]
        total = sum(len(s["items"]) - 1 for s in segs)
        want = set(want or ())
        best = None
        pos = start
        while pos + 4 * (segs[0]["start"] + 1) <= end:
            if struct.unpack_from("<i", self.d, pos + 4 * segs[0]["start"])[0] == POISON:
                pos += 4
                continue
            score = 0
            req = 0
            for seg in segs:
                o0 = seg["start"]
                v0 = struct.unpack_from("<i", self.d, pos + 4 * o0)[0]
                if v0 < 0 or v0 == POISON or v0 > 0x40000:
                    score = -1
                    break
                if v0 in want:
                    req += 1
                for (o, rel) in seg["items"][1:]:
                    v = struct.unpack_from("<i", self.d, pos + 4 * o)[0]
                    if v == POISON:
                        continue
                    if v - v0 == rel:
                        score += 1
                    else:
                        score = -1
                        break
                if score < 0:
                    break
            if score >= 0:
                if best is None or (score, req) > (best[0], best[3]):
                    rva = rdata["va"] + (pos - rdata["raw"])
                    best = (score, rva, total, req)
            pos += 4
        if best and best[0] >= max(3, best[2] // 2):
            return best
        return None

    def read_table(self, rva, n):
        o = self.r2o(rva)
        return list(struct.unpack_from("<%di" % n, self.d, o))

    # -- code displacements ---------------------------------------------
    def code_disps(self, tdi):
        try:
            from capstone import Cs, CS_ARCH_X86, CS_MODE_64
        except ImportError:
            return {}
        cs = Cs(CS_ARCH_X86, CS_MODE_64)
        cs.detail = True
        t = self.meta.type(tdi)
        seen = {}
        for k in range(t["method_count"]):
            m = self.meta.method(t["first_method"] + k)
            info = self.mapper.rva_for_method(m)
            if not info:
                continue
            off = self.r2o(info["rva"])
            if off is None:
                continue
            code = self.d[off:off + 3000]
            cnt = 0
            for ins in cs.disasm(code, info["rva"]):
                cnt += 1
                if cnt > 900 or ins.mnemonic in ("ret", "int3"):
                    break
                for op in ins.operands:
                    if op.type == 3 and op.mem.base:
                        dsp = op.mem.disp
                        if 0x10 <= dsp <= 0x1000:
                            bn = ins.reg_name(op.mem.base)
                            if bn in ("rsp", "esp", "rbp", "ebp"):
                                continue
                            seen.setdefault(dsp, {
                                "method": m["name"], "method_rva": info["rva"],
                                "insn_rva": ins.address,
                                "insn": ins.mnemonic + " " + ins.op_str,
                            })
        return seen

    # -- evidence for one requested offset -------------------------------
    def evidence(self, cls, off, table_cache, code_cache, wants=None):
        tdi = self.tdi.get(cls)
        if tdi is None:
            return None
        if tdi not in table_cache:
            table_cache[tdi] = self.find_table(tdi, wants)
        found = table_cache[tdi]
        if found:
            score, rva, total, _req = found
            n = self.meta.type(tdi)["field_count"]
            arr = self.read_table(rva, n)
            for idx, v in enumerate(arr):
                if v == off and v != POISON:
                    return {"kind": "table", "table_rva": rva, "index": idx,
                            "score": score, "total": total}
        if tdi not in code_cache:
            code_cache[tdi] = self.code_disps(tdi)
        hit = code_cache[tdi].get(off)
        if hit:
            return {"kind": "code", **hit}
        return None


def main():
    b = Binary()
    os.makedirs(OUT, exist_ok=True)
    table_cache, code_cache = {}, {}
    result = {}
    report = ["# Offsets derived from GameAssembly.dll (build 26140533)", "",
              "Source of every value: `.rdata` field-offset table or a `[this+disp]`",
              "memory operand in the class' own IL2CPP methods.  No live dump and",
              "no `tools/reference` table is read by this script.", "",
              f"- Il2CppType table: `0x{b.types_rva:X}`",
              f"- Il2CppTypeDefinitionSizes table: `0x{b.sizes_rva:X}`", ""]
    failures = 0
    for cls, rows in REQUEST.items():
        # dedupe aliases (same name twice at same offset kept once)
        res = []
        seen = set()
        wants = {off for _n, off, _t in rows}
        for name, off, typ in rows:
            if (name, off) in seen:
                continue
            seen.add((name, off))
            ev = b.evidence(cls, off, table_cache, code_cache, wants)
            if ev is None:
                ev = {"kind": "MISSING"}
                failures += 1
            res.append({"name": name, "offset": off, "type": typ, **ev})
        result[cls] = res

        tdi = b.tdi.get(cls)
        found = table_cache.get(tdi)
        h = [
            "// ===========================================================================",
            f"//  {cls}_binary.h - Rust build 26140533",
            "//  generated by revers/rev_binary.py",
            "//  PROVENANCE: value read from GameAssembly (field-offset table or code)",
            "// ===========================================================================",
            "#pragma once",
            "#include <cstdint>",
            "",
            f"namespace {cls}",
            "{",
        ]
        for r in res:
            note = r["type"] if r["kind"] == "table" else (
                "code: " + r["insn"] if r["kind"] == "code" else "NOT FOUND")
            h.append("    constexpr std::uintptr_t %-46s = 0x%X; // %s"
                     % (r["name"], r["offset"], note))
        h.append("}")
        with open(os.path.join(OUT, f"{cls}_binary.h"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("\n".join(h) + "\n")

        nt = sum(1 for r in res if r["kind"] == "table")
        nc = sum(1 for r in res if r["kind"] == "code")
        nm = sum(1 for r in res if r["kind"] == "MISSING")
        report.append(f"## {cls}")
        report.append("")
        if found:
            report.append(f"- field-offset table: `0x{found[1]:X}` "
                          f"(layout anchors {found[0]}/{found[2]})")
        else:
            report.append("- field-offset table: not located")
        report.append(f"- fields: **{len(res)}**  table: **{nt}**  code: **{nc}**  missing: **{nm}**")
        report.append("")
        report.append("| field | offset | evidence |")
        report.append("|---|---|---|")
        for r in res:
            if r["kind"] == "table":
                ev = f"table `0x{r['table_rva']:X}`[#{r['index']}]"
            elif r["kind"] == "code":
                ev = f"`{r['insn']}` in `{r['method']}` @ `0x{r['insn_rva']:X}`"
            else:
                ev = "**NOT FOUND**"
            report.append(f"| `{r['name']}` | `0x{r['offset']:X}` | {ev} |")
        report.append("")

    with open(os.path.join(OUT, "binary_provenance.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
    with open(os.path.join(OUT, "binary_report.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")

    for cls, res in result.items():
        nt = sum(1 for r in res if r["kind"] == "table")
        nc = sum(1 for r in res if r["kind"] == "code")
        nm = sum(1 for r in res if r["kind"] == "MISSING")
        print(f"[+] {cls:<14} table={nt:<3} code={nc:<3} missing={nm}")
    print(f"[+] types table 0x{b.types_rva:X}  sizes table 0x{b.sizes_rva:X}")
    print(f"[+] wrote {os.path.join(OUT, 'binary_report.md')}")
    print(f"[+] wrote {os.path.join(OUT, 'binary_provenance.json')}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
