package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.controller.type.TypeToClient;
import com.deepblue.yd_jz.dao.type.Type;
import com.deepblue.yd_jz.dao.type.TypeDao;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
public class TypeService {

    @Autowired
    TypeDao typeDao;

    @Transactional(rollbackFor = Exception.class)
    public void addType(Type type) {
      /*  if (type.getParent()!=-1){
            Type parentType = typeDao.queryTypeSingle(type.getParent()).get(0);
            if (parentType!=null){
                parentType.setHasChild(true);
                typeDao.updateType(parentType);
            }
        }*/
        typeDao.addType(type);
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateType(Type type) {
        typeDao.updateType(type);
    }

    @Transactional(rollbackFor = Exception.class)
    public void disableType(int id) {
        typeDao.setDisableTypeChild(id);
        typeDao.disableType(id);
    }

    @Transactional(rollbackFor = Exception.class)
    public List<Type> queryTypeList(int parent) {
        return typeDao.queryTypeList(parent);
    }

    @Transactional(rollbackFor = Exception.class)
    public Type queryTypeSingle(int id) {
        List<Type> types = typeDao.queryTypeSingle(id);
        if (types.size() > 0) {
            return types.get(0);
        } else {
            return null;
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public List<TypeToClient> queryAllType() {
        List<Type> allTypes = typeDao.queryAllType();
        List<TypeToClient> toClients = new ArrayList<>();
        for (Type type : allTypes) {
            if (type.getParent() == -1) {
                TypeToClient typeToClient = new TypeToClient();
                typeToClient.setId(type.getId());
                typeToClient.setParent(type.getParent());
                typeToClient.settName(type.gettName());
                toClients.add(typeToClient);
            }
        }
        for (Type type : allTypes) {
            if (type.getParent()!=-1){
                TypeToClient child = new TypeToClient();
                child.setId(type.getId());
                child.setParent(type.getParent());
                child.settName(type.gettName());

                for (TypeToClient parent: toClients) {
                    if (parent.getId() == child.getParent()){
                        if (parent.getChildrenTypes()==null){
                            List<TypeToClient> children = new ArrayList<>();
                            parent.setChildrenTypes(children);
                        }
                        parent.getChildrenTypes().add(child);
                    }
                }
            }
        }

        return toClients;
    }
}
